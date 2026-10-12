"""Independent acceptance checks against fixed reference vectors and malformed inputs."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from evaluator.common import canonical
from evaluator.intake import PROFILE, TRACKS
from evaluator.verifier import Verifier, decode_hex, pinned_bls

ROOT = Path(__file__).resolve().parents[1]


class OutputVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        profiles = json.loads((ROOT / PROFILE).read_text())
        cls.verifiers = {t: Verifier(profiles, t) for t in TRACKS}
        cls.vectors = json.loads((ROOT / "tests/fixtures/production-v1-vectors.json").read_text())

    def test_all_fixed_vectors_including_identity_and_inverse(self):
        for track, verifier in self.verifiers.items():
            for vector in self.vectors[track]:
                with self.subTest(track=track, input=vector["input"]):
                    self.assertTrue(verifier.verify(vector["input"], vector["output"]))

    def test_wrong_valid_answers_fail(self):
        for track, verifier in self.verifiers.items():
            vectors = self.vectors[track]
            self.assertFalse(verifier.verify(vectors[1]["input"], vectors[2]["output"]))
            self.assertFalse(verifier.verify(vectors[0]["input"], vectors[1]["output"]))

    def test_canonical_values_and_duplicate_keys(self):
        for value in (True, 1, "01", "0x"+"0"*64, "A"*64, "0"*65, "f"*64):
            with self.assertRaises(ValueError):
                decode_hex(value, 64, 23)
        verifier = self.verifiers[TRACKS[0]]
        for output in (b'{"x":"'+b'0'*64+b'","x":"'+b'0'*64+b'"}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                verifier.verify_bytes(b'{"Q":null}', output)

    def test_off_curve_out_of_range_and_wrong_subgroup(self):
        for track, verifier in self.verifiers.items():
            width = verifier.width
            for point in ({"x": "0"*width, "y": "0"*width},
                          {"x": f"{verifier.p:0{width}x}", "y": "0"*width},
                          {"x": "0"*width, "y": "0"*width, "extra": 1}):
                with self.assertRaises(ValueError):
                    verifier.point(point)
        # (0,2) is on BLS12-381's full curve but outside its prime-order G1 subgroup.
        with self.assertRaises(ValueError):
            self.verifiers[TRACKS[1]].point({"x": "0"*96, "y": f"{2:096x}"})

    def test_gt_length_zero_nonmember_and_all_coefficients(self):
        verifier = self.verifiers[TRACKS[1]]
        for value in (["0"*96]*12, ["0"*96]*11, [f"{2:096x}"]+["0"*96]*11):
            with self.assertRaises(ValueError):
                verifier.target_gt(value)
        # The accepted vector is a full field element, not its first coefficient or Miller output.
        vector = self.vectors[TRACKS[1]][1]
        wrong = copy.deepcopy(vector["input"])
        wrong["z"][11] = "0"*96
        with self.assertRaises(ValueError):
            verifier.verify(wrong, vector["output"])
        b = verifier.bls
        raw = b.pairing(b.G2, b.G1, final_exponentiate=False)
        with self.assertRaises(ValueError):
            verifier.target_gt([f"{int(c):096x}" for c in raw.coeffs])

    def test_challenge_sampling_includes_endpoints_without_leaking_scalar(self):
        for track, verifier in self.verifiers.items():
            for index, scalar in ((0, 0), (1, 1), (3, verifier.r-1)):
                with patch("evaluator.verifier.secrets.randbelow", return_value=scalar):
                    challenge = verifier.challenge()
                self.assertEqual(challenge, self.vectors[track][index]["input"])
                self.assertEqual(set(challenge), {"Q" if track == TRACKS[0] else "z"})

    def test_reference_source_hash_mismatch_fails(self):
        reference = copy.deepcopy(self.verifiers[TRACKS[1]].target["pairing"]["reference"])
        first = next(iter(reference["source_sha256"]))
        reference["source_sha256"][first] = "0"*64
        with self.assertRaises(ValueError):
            pinned_bls(canonical(reference).decode())


if __name__ == "__main__":
    unittest.main()
