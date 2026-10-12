"""Offline checks of draft invariants; no scientific qualification or live runner."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prelaunch", ROOT / "scripts/prelaunch.py")
prelaunch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prelaunch)


class DraftGates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "starter"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".env", "scores", "reports"))

    def change(self, path, mutation):
        file = self.root / path
        value = json.loads(file.read_text())
        mutation(value)
        file.write_text(json.dumps(value))

    def reject(self):
        with self.assertRaises((ValueError, KeyError, TypeError, OSError)):
            prelaunch.validate(self.root)

    def test_draft_is_consistent_but_not_ready(self):
        manifest, profiles, cost = prelaunch.validate(self.root)
        self.assertEqual({t["name"] for t in manifest["tracks"]},
                         {"secp256k1-ecdlp", "bls12-381-invert-g1"})
        self.assertTrue(prelaunch.readiness_errors(profiles, cost))

    def test_protected_paths_are_not_candidate_editable(self):
        self.change("benchmark.json", lambda v: v["tracks"][0].update(
            editablePaths=["target-profiles"]))
        self.reject()

    def test_extra_track_rejected(self):
        self.change("benchmark.json", lambda v: v["tracks"].append(
            dict(v["tracks"][0], name="p256-ecdlp")))
        self.reject()

    def test_target_substitution_rejected(self):
        self.change("target-profiles/production-v2.json", lambda v:
                    v["targets"][0].update(id="p256-ecdlp"))
        self.reject()

    def test_automatic_promotion_rejected(self):
        self.change("benchmark.json", lambda v: v["tracks"][0].update(
            promotionMode="auto"))
        self.reject()

    def test_candidate_score_command_rejected(self):
        self.change("benchmark.json", lambda v: v["tracks"][0].update(
            benchmarkCommand=["python3", "candidates/attack.py"]))
        self.reject()

    def test_changed_metric_rejected(self):
        self.change("cost-models/classical-group-work-v2.json", lambda v: v.update(
            metric="largest_toy_curve"))
        self.reject()

    def test_changed_success_requirement_rejected(self):
        self.change("cost-models/classical-group-work-v2.json", lambda v: v.update(
            success_probability_minimum=0.01))
        self.reject()

    def test_restricted_target_rejected(self):
        self.change("target-profiles/production-v2.json", lambda v:
                    v["targets"][0].update(scope="restricted-scalar-interval"))
        self.reject()

    def test_invented_baseline_rejected(self):
        self.change("target-profiles/production-v2.json", lambda v:
                    v["targets"][0].update(qualified_baseline={"time_log2": 128}))
        self.reject()

    def test_status_cannot_assert_qualification(self):
        for path in ("target-profiles/production-v2.json",
                     "cost-models/classical-group-work-v2.json"):
            with self.subTest(path=path):
                original = (self.root / path).read_text()
                self.change(path, lambda v: v.update(state="plausible_not_refuted"))
                self.reject()
                (self.root / path).write_text(original)

    def test_duplicate_json_keys_and_nonfinite_numbers_rejected(self):
        file = self.root / "bad.json"
        for content in ('{"a": 1, "a": 2}', '{"a": NaN}', '{"a": Infinity}'):
            with self.subTest(content=content):
                file.write_text(content)
                with self.assertRaises(ValueError):
                    prelaunch.read_json(file)

    def test_noncanonical_paths_rejected(self):
        for path in ("../scores", "/tmp/scores", "a/../scores", "a//b",
                     "a\\b", "./scores", ""):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    prelaunch.relative_path(path)

    def test_symlinked_candidate_root_rejected(self):
        manifest, _, _ = prelaunch.validate(self.root)
        candidate = self.root / manifest["tracks"][0]["editablePaths"][0]
        shutil.rmtree(candidate)
        candidate.symlink_to(self.root / "docs", target_is_directory=True)
        self.reject()

    def test_stale_score_rejected(self):
        manifest, _, _ = prelaunch.validate(self.root)
        score = self.root / manifest["tracks"][0]["scorePath"]
        score.parent.mkdir(parents=True)
        score.write_text('{"time_log2": 1}')
        self.reject()

    def test_cli_emits_no_score_and_never_runs_candidate_code(self):
        candidate = self.root / "candidates/secp256k1-ecdlp/attack.py"
        marker = self.root / "candidate-was-executed"
        candidate.write_text("from pathlib import Path\n"
                             "Path('candidate-was-executed').touch()\n"
                             "raise RuntimeError('candidate execution forbidden')\n")
        for arguments, expected in (([], 0), (["--require-ready"], 2),
                                    (["--track", "unknown"], 1)):
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, "scripts/prelaunch.py", *arguments],
                                        cwd=self.root, capture_output=True, text=True,
                                        timeout=10)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertFalse(marker.exists())
                self.assertFalse((self.root / ".yukon/scores").exists())


if __name__ == "__main__":
    unittest.main()
