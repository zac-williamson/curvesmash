"""Independent arithmetic checks of public profile fixtures, not an attack verifier."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROFILES = json.loads((ROOT / "target-profiles/production-v1.json").read_text())
VECTORS = json.loads((ROOT / "tests/fixtures/production-v1-vectors.json").read_text())


def add(a, b, p):
    if a is None:
        return b
    if b is None:
        return a
    x, y = a
    u, v = b
    if x == u and (y + v) % p == 0:
        return None
    m = (3*x*x * pow(2*y, -1, p) if a == b else
         (v-y) * pow(u-x, -1, p)) % p
    z = (m*m-x-u) % p
    return z, (m*(x-z)-y) % p


def multiply(point, n, p):
    result = None
    while n:
        if n & 1:
            result = add(result, point, p)
        point = add(point, point, p)
        n >>= 1
    return result


def gt_multiply(a, b, p):
    coefficients = [0] * 23
    for i in range(12):
        for j in range(12):
            coefficients[i+j] += a[i] * b[j]
    # w^12 = 2*w^6 - 2 in the specified polynomial basis.
    for k in range(22, 11, -1):
        coefficients[k-6] += 2 * coefficients[k]
        coefficients[k-12] -= 2 * coefficients[k]
    return [c % p for c in coefficients[:12]]


def gt_power(a, n, p):
    result = [1] + [0] * 11
    while n:
        if n & 1:
            result = gt_multiply(result, a, p)
        a = gt_multiply(a, a, p)
        n >>= 1
    return result


class ProfileArithmetic(unittest.TestCase):
    def decode_point(self, value, width, p):
        if value is None:
            return None
        self.assertEqual(set(value), {"x", "y"})
        for c in value.values():
            self.assertEqual(len(c), 2 * width)
            self.assertEqual(c, format(int(c, 16), f"0{2*width}x"))
            self.assertLess(int(c, 16), p)
        return int(value["x"], 16), int(value["y"], 16)

    def test_generators_and_point_vectors(self):
        for target in PROFILES["targets"]:
            name = target["id"]
            p = int(target["field_modulus"], 16)
            r = int(target["subgroup_order"], 16)
            is_dlp = name == "secp256k1-ecdlp"
            width, b = (32, 7) if is_dlp else (48, 4)
            generator = self.decode_point(target["generator_P" if is_dlp else "generator_P0"], width, p)
            self.assertEqual((generator[1]**2 - generator[0]**3 - b) % p, 0)
            self.assertIsNone(multiply(generator, r, p))
            for scalar, vector in zip((0, 1, 2, r-1), VECTORS[name], strict=True):
                with self.subTest(target=name, scalar=scalar):
                    encoded = vector["input"]["Q"] if is_dlp else vector["output"]["P"]
                    point = self.decode_point(encoded, width, p)
                    self.assertEqual(point, multiply(generator, scalar, p))
                    if is_dlp:
                        self.assertEqual(int(vector["output"]["x"], 16), scalar)

    def test_gt_vectors_in_specified_polynomial_basis(self):
        target = PROFILES["targets"][1]
        p, r = int(target["field_modulus"], 16), int(target["subgroup_order"], 16)
        values = []
        for vector in VECTORS[target["id"]]:
            encoded = vector["input"]["z"]
            self.assertEqual(len(encoded), 12)
            for c in encoded:
                self.assertEqual(c, format(int(c, 16), "096x"))
                self.assertLess(int(c, 16), p)
            z = [int(c, 16) for c in encoded]
            self.assertNotEqual(z, [0] * 12)
            self.assertEqual(gt_power(z, r, p), [1] + [0] * 11)
            values.append(z)
        identity, generator, doubled, negative = values
        self.assertEqual(identity, [1] + [0] * 11)
        self.assertNotEqual(generator, identity)
        self.assertEqual(doubled, gt_multiply(generator, generator, p))
        self.assertEqual(identity, gt_multiply(generator, negative, p))

    def test_profile_cost_version_and_reference_lock(self):
        cost = json.loads((ROOT / "cost-models/classical-word-ram-v1.json").read_text())
        self.assertEqual(PROFILES["cost_model"], cost["id"])
        self.assertEqual(cost["success_probability_minimum"], 0.39)
        self.assertEqual(cost["word_bits"], 256)
        self.assertEqual(set(cost["primitive_operations"].values()), {1})
        reference = PROFILES["targets"][1]["pairing"]["reference"]
        self.assertEqual(reference["commit"], "04151f01f59f902ab932a51e0ca0ebce3883fc51")
        self.assertEqual(len(reference["source_sha256"]), 4)
        for digest in reference["source_sha256"].values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_bls_family_cofactor_twist_and_embedding(self):
        target = PROFILES["targets"][1]
        p, r = int(target["field_modulus"], 16), int(target["subgroup_order"], 16)
        x = int(target["parameter_x"], 16)
        self.assertEqual(r, x**4-x**2+1)
        self.assertEqual(p, ((x-1)**2*r)//3+x)
        self.assertEqual(int(target["cofactor_G1"], 16)*r, p-x)

        def fq2_multiply(a, b):
            return ((a[0]*b[0]-a[1]*b[1]) % p,
                    (a[0]*b[1]+a[1]*b[0]) % p)

        q = target["generator_Q0"]
        qx = tuple(int(c, 16) for c in q["x"])
        qy = tuple(int(c, 16) for c in q["y"])
        cube = fq2_multiply(fq2_multiply(qx, qx), qx)
        self.assertEqual(fq2_multiply(qy, qy), tuple((c+4) % p for c in cube))
        # u=w^6-1 must satisfy u^2=-1 in the pinned Fp12 representation.
        u = [p-1] + [0]*5 + [1] + [0]*5
        self.assertEqual(gt_multiply(u, u, p), [p-1]+[0]*11)


if __name__ == "__main__":
    unittest.main()
