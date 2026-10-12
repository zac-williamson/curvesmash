"""Organizer mathematical output checks. These do not measure attack complexity."""
from functools import lru_cache
import importlib.metadata
from pathlib import Path
import re
import secrets

from .common import exact, parse, read_file, require, sha
from .intake import PROFILE, TRACKS


def decode_hex(value, width, modulus):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{"+str(width)+"}", value),
            "Noncanonical field/scalar encoding")
    result = int(value, 16)
    require(result < modulus, "Field/scalar value out of range")
    return result


def add(a, b, p):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    u, v = b
    if x == u and (y+v) % p == 0:
        return None
    slope = ((3*x*x) * pow(2*y, -1, p) if a == b else
             (v-y) * pow(u-x, -1, p)) % p
    rx = (slope*slope-x-u) % p
    return rx, (slope*(x-rx)-y) % p


def multiply(a, n, p):
    result = None
    while n:
        if n & 1:
            result = add(result, a, p)
        a = add(a, a, p)
        n >>= 1
    return result


@lru_cache(maxsize=4)
def pinned_bls(reference_text):
    reference = parse(reference_text)
    require(importlib.metadata.version("py-ecc") == "8.0.0", "Wrong pairing reference version")
    import py_ecc
    root = Path(py_ecc.__file__).parent.parent
    for path, expected in reference["source_sha256"].items():
        require(sha(read_file(root / path)) == expected, "Pairing reference source mismatch")
    from py_ecc import optimized_bls12_381 as bls
    return bls


class Verifier:
    def __init__(self, profiles, track):
        require(track in TRACKS, "Unknown target")
        self.track = track
        self.target = next(t for t in profiles["targets"] if t["id"] == track)
        self.p = int(self.target["field_modulus"], 16)
        self.r = int(self.target["subgroup_order"], 16)
        self.width = 64 if track == TRACKS[0] else 96
        generator = self.target["generator_P" if track == TRACKS[0] else "generator_P0"]
        self.generator = self.point(generator)
        require(self.generator is not None, "Generator cannot be infinity")
        self.bls = None
        if track == TRACKS[1]:
            from .common import canonical
            self.bls = pinned_bls(canonical(self.target["pairing"]["reference"]).decode())
            require(self.bls.field_modulus == self.p and self.bls.curve_order == self.r,
                    "Pairing library constants differ from profile")
            self.q0 = self.bls.G2
            x, y = self.bls.normalize(self.q0)
            actual = {"x": [f"{int(c):096x}" for c in x.coeffs],
                      "y": [f"{int(c):096x}" for c in y.coeffs]}
            require(actual == self.target["generator_Q0"], "Wrong G2 generator")
            self.base = self.bls.pairing(self.q0, self.bls_point(self.generator),
                                       final_exponentiate=True)
            require(self.base != self.bls.FQ12.one() and self.base**self.r == self.bls.FQ12.one(),
                    "Pairing base must generate GT")

    @classmethod
    def from_evidence(cls, record):
        evidence = record["evidence"]
        return cls(parse(evidence["files"][PROFILE]["text"]), evidence["track"])

    def point(self, value):
        if value is None:
            return None
        exact(value, ("x", "y"))
        x = decode_hex(value["x"], self.width, self.p)
        y = decode_hex(value["y"], self.width, self.p)
        require((y*y-x*x*x-(7 if self.track == TRACKS[0] else 4)) % self.p == 0,
                "Off-curve point")
        point = (x, y)
        require(multiply(point, self.r, self.p) is None, "Point outside target subgroup")
        return point

    def encode_point(self, point):
        return None if point is None else {"x": f"{point[0]:0{self.width}x}",
                                           "y": f"{point[1]:0{self.width}x}"}

    def bls_point(self, point):
        if point is None:
            return self.bls.Z1
        return self.bls.FQ(point[0]), self.bls.FQ(point[1]), self.bls.FQ.one()

    def target_gt(self, value):
        require(type(value) is list and len(value) == 12, "GT needs exactly 12 coefficients")
        coefficients = [decode_hex(x, 96, self.p) for x in value]
        require(any(coefficients), "Zero is not in GT")
        gt = self.bls.FQ12(coefficients)
        require(gt**self.r == self.bls.FQ12.one(), "Value outside GT")
        return gt

    def challenge(self):
        # secrets.randbelow uses rejection sampling; never return the sampling scalar.
        scalar = secrets.randbelow(self.r)
        if self.track == TRACKS[0]:
            return {"Q": self.encode_point(multiply(self.generator, scalar, self.p))}
        z = self.base**scalar
        return {"z": [f"{int(c):096x}" for c in z.coeffs]}

    def verify(self, challenge, output):
        if self.track == TRACKS[0]:
            exact(challenge, ("Q",))
            exact(output, ("x",))
            q = self.point(challenge["Q"])
            x = decode_hex(output["x"], 64, self.r)
            return multiply(self.generator, x, self.p) == q
        exact(challenge, ("z",))
        exact(output, ("P",))
        z = self.target_gt(challenge["z"])
        p = self.point(output["P"])
        return self.bls.pairing(self.q0, self.bls_point(p), final_exponentiate=True) == z

    def verify_bytes(self, challenge, output):
        return self.verify(parse(challenge, 65536), parse(output, 65536))
