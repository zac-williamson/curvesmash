"""Adversarial organizer fixtures; synthetic approvals never leave temporary roots."""
import copy
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from evaluator import common, intake, review, provider, experiments

ROOT = Path(__file__).resolve().parents[1]
TRACK = intake.TRACKS[0]


class Evaluation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "organizer"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".env", "scores", "reports"))
        # Organizer fixtures never load real production history or contact GitHub.
        (self.root / "reorg/plan.json").write_text('{"schema_version":1,"entries":[]}\n')
        self.policy = common.read_json(self.root / intake.POLICY)
        self.keys = {}
        for name in (*review.OBLIGATIONS, "defender", "adjudicator", "execution", "definitions"):
            key = Ed25519PrivateKey.generate()
            self.keys[name] = key.private_bytes_raw()
            registry = "definition_approvers" if name == "definitions" else "reviewers"
            self.policy[registry][name] = {"public_key": key.public_key().public_bytes_raw().hex(),
                                           "roles": [name]}
        self.save_policy()
        self.record = intake.build_evidence(self.root, TRACK)

    def save_policy(self):
        (self.root / intake.POLICY).write_text(json.dumps(self.policy))

    def change(self, path, mutation):
        file = self.root / path
        value = json.loads(file.read_text())
        mutation(value)
        file.write_text(json.dumps(value))

    def signed_reviews(self, record=None):
        record = record or self.record
        result = []
        for role in review.OBLIGATIONS:
            body = review.template(record, role, role)
            for item in body["obligations"]:
                item.update(status="supported", reason="Synthetic fixture: organizer gate test only.")
            for item in body["heuristics"]:
                item.update(status="established", reason="Synthetic fixture only.")
            result.append(review.sign(body, self.keys[role]))
        return result

    def approval(self, record=None):
        record = record or self.record
        return review.sign({"kind": "definitions", "reviewer": "definitions",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "binding": review.definitions_binding(record["evidence"]),
            "decision": "approved", "reason": "Synthetic fixture only; not scientific review."},
            self.keys["definitions"])

    def dossier(self, reviews=None, record=None, **kwargs):
        record = record or self.record
        return review.aggregate(record, reviews if reviews is not None else self.signed_reviews(record),
                                definition_approval=self.approval(record), **kwargs)

    def resign(self, records, role, mutate):
        records = copy.deepcopy(records)
        for index, record in enumerate(records):
            if record["body"]["role"] == role:
                body = record["body"]
                mutate(body)
                records[index] = review.sign(body, self.keys[role])
        return records

    def finding(self, severity="fatal"):
        records = self.signed_reviews()
        def mutate(body):
            body["findings"].append({"id": "F1", "severity": severity,
                "reason": "Synthetic objection for challenge protocol testing.",
                "citations": body["obligations"][0]["citations"],
                "obligations": ["correctness"], "heuristic_ids": []})
            body["obligations"][0]["status"] = "unresolved"
        return self.resign(records, "cryptanalysis", mutate)

    def challenge(self, records, decision="dismissed", discharged=None):
        initial = next(r for r in records if r["body"]["role"] == "cryptanalysis")
        shared = {"issued_at": datetime.now(timezone.utc).isoformat(), "binding": self.record["binding"],
            "review_sha256": common.digest(initial), "finding_id": "F1",
            "reason": "Synthetic challenge fixture only.",
            "citations": initial["body"]["findings"][0]["citations"]}
        defense = review.sign(dict(shared, kind="defense", reviewer="defender"), self.keys["defender"])
        adjudication = review.sign(dict(shared, kind="adjudication", reviewer="adjudicator",
            defense_sha256=common.digest(defense), decision=decision,
            discharged_obligations=discharged if discharged is not None else
            (["correctness"] if decision == "dismissed" else [])), self.keys["adjudicator"])
        return {"defense": defense, "adjudication": adjudication}

    def test_both_packages_intake_without_execution(self):
        for track in intake.TRACKS:
            with self.subTest(track=track):
                record = intake.build_evidence(self.root, track)
                self.assertEqual(record, intake.build_evidence(self.root, track))
                self.assertEqual(intake.check_evidence(record)["track"], track)
                self.assertEqual(review.aggregate(record, [])["outcome"], "pending_review")
        attack = self.root / "candidates" / TRACK / "attack.py"
        attack.write_text("raise RuntimeError('must never execute on host')")
        with patch("subprocess.Popen", side_effect=AssertionError("Execution attempted")):
            changed = intake.build_evidence(self.root, TRACK)
        self.assertNotEqual(changed["binding"], self.record["binding"])

    def test_every_byte_is_bound(self):
        for path in ("candidates/"+TRACK+"/README.md", intake.PROFILE, intake.COST,
                     intake.POLICY, "evaluator/provider.py", "requirements.lock"):
            with self.subTest(path=path):
                file = self.root / path
                data = file.read_bytes()
                file.write_bytes(data+b"\n")
                try:
                    if path in (intake.PROFILE, intake.COST):
                        with self.assertRaises(ValueError):
                            intake.build_evidence(self.root, TRACK)
                    else:
                        changed = intake.build_evidence(self.root, TRACK)
                        self.assertNotEqual(changed["binding"], self.record["binding"])
                finally:
                    file.write_bytes(data)

    def test_symlinks_hardlinks_fifo_and_directory_links_rejected(self):
        folder = self.root / "candidates" / TRACK
        target = folder / "malicious"
        for kind in ("symlink", "hardlink", "fifo", "directory"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    target.symlink_to(self.root / intake.POLICY)
                elif kind == "hardlink":
                    os.link(folder / "proof.md", target)
                elif kind == "fifo":
                    os.mkfifo(target)
                else:
                    target.symlink_to(self.root, target_is_directory=True)
                with self.assertRaises((ValueError, OSError)):
                    intake.build_evidence(self.root, TRACK)
                target.unlink()

    def test_limits_encoding_and_paths(self):
        folder = self.root / "candidates" / TRACK
        target = folder / "bad"
        for data in (b"\x00", b"\xff", b"a"*(common.MAX_BYTES+1)):
            target.write_bytes(data)
            with self.assertRaises((ValueError, UnicodeError)):
                intake.snapshot(folder)
        target.unlink()
        for name in ("../a", "/a", "a//b", "a/./b", "a\\b", "", "a,b"):
            with self.assertRaises(ValueError):
                common.relative(name)
        for index in range(130):
            (folder / str(index)).touch()
        with self.assertRaises(ValueError):
            intake.snapshot(folder)

    def test_json_duplicates_nonfinite_and_depth(self):
        for data in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}', '['*34+'0'+']'*34):
            with self.assertRaises(ValueError):
                common.parse(data)

    def test_claim_gates(self):
        path = "candidates/"+TRACK+"/claim.json"
        file = self.root / path
        original = file.read_text()
        mutations = [lambda v: v.update(target_id=intake.TRACKS[1]),
            lambda v: v.update(target_profile_sha256="0"*64),
            lambda v: v.update(review_status="accepted"), lambda v: v.update(unexpected=True),
            lambda v: v.update(proof="../README.md"),
            lambda v: v["claim"].update(success_probability=True),
            lambda v: v["claim"].update(success_probability=0.38),
            lambda v: v["claim"].update(success_probability=10**511),
            lambda v: v["claim"].update(time_log2=float("nan")),
            lambda v: v["claim"].update(work_budget_word_operations="01")]
        for mutation in mutations:
            file.write_text(original)
            self.change(path, mutation)
            with self.assertRaises(ValueError):
                intake.build_evidence(self.root, TRACK)

    def test_prose_accounting_needs_no_structured_ledger(self):
        self.assertNotIn("resource_ledger", self.record["evidence"]["claim"])
        self.assertNotIn("candidate/ledger.json", self.record["evidence"]["files"])
        path = "candidates/"+TRACK+"/claim.json"
        self.change(path, lambda v: v["claim"].update(memory_log2_bytes=262))
        with self.assertRaises(ValueError):
            intake.build_evidence(self.root, TRACK)

    def test_policy_cannot_reduce_review_standard(self):
        self.policy["minimum_distinct_initial_reviewers"] = 1
        self.save_policy()
        with self.assertRaises(ValueError):
            intake.build_evidence(self.root, TRACK)

    def test_rounding_near_large_powers_of_two_and_separate_definition_authority(self):
        self.assertEqual(intake.log2_upper(1 << 1700), 1700)
        self.assertEqual(intake.log2_upper((1 << 1700)+1), 1700.000001)
        self.policy["definition_approvers"]["definitions"]["public_key"] = \
            self.policy["reviewers"]["cost"]["public_key"]
        with self.assertRaises(ValueError):
            intake.validate_policy(self.policy)

    def test_valid_synthetic_end_to_end_score(self):
        dossier = self.dossier()
        self.assertEqual(dossier["outcome"], "plausible_not_refuted")
        result = review.score(self.record, dossier)
        self.assertEqual(result["timeLog2"], self.record["evidence"]["claim"]["claim"]["time_log2"])
        self.assertEqual(result["promotionMode"], "manual")
        self.assertEqual(result["claim_kind"], "generic-accounting-control")

    def test_pending_cannot_score_or_fake_outcome(self):
        dossier = review.aggregate(self.record, [])
        dossier["outcome"] = "plausible_not_refuted"
        with self.assertRaises(ValueError):
            review.score(self.record, dossier)

    def test_library_scorer_rejects_mutated_envelope_and_claim_copy(self):
        dossier = self.dossier()
        altered = copy.deepcopy(self.record)
        altered["evidence"]["claim"]["claim"]["time_log2"] = 1
        with self.assertRaises(ValueError):
            review.score(altered, dossier)
        altered["binding"] = common.digest(altered["evidence"])
        with self.assertRaises(ValueError):
            intake.check_evidence(altered)

    def test_missing_review_blocks_and_extra_definition_approval_is_not_required(self):
        self.assertEqual(self.dossier(self.signed_reviews()[:-1])["outcome"], "infra_failed")
        self.assertEqual(review.aggregate(self.record, self.signed_reviews())["outcome"], "plausible_not_refuted")

    def test_signature_binding_authority_and_freshness(self):
        records = self.signed_reviews()
        corrupt = copy.deepcopy(records)
        corrupt[0]["body"]["obligations"][0]["reason"] = "tampered"
        with self.assertRaises(ValueError):
            self.dossier(corrupt)
        mutations = [lambda b: b.update(binding="0"*64), lambda b: b.update(reviewer="unknown"),
            lambda b: b.update(issued_at=(datetime.now(timezone.utc)-timedelta(days=31)).isoformat()),
            lambda b: b.update(issued_at=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()),
            lambda b: b.update(role="cost")]
        for mutation in mutations:
            with self.assertRaises(ValueError):
                self.dossier(self.resign(records, "evaluability", mutation))

    def test_duplicate_missing_obligations_and_invalid_citations(self):
        records = self.signed_reviews()
        for mutation in (lambda b: b["obligations"].pop(),
            lambda b: b["obligations"][0].update(id="algorithm"),
            lambda b: b["obligations"][0]["citations"][0].update(path="/etc/passwd"),
            lambda b: b["obligations"][0]["citations"][0].update(sha256="0"*64),
            lambda b: b["obligations"][0]["citations"][0].update(lines=[0, 1])):
            with self.assertRaises(ValueError):
                self.dossier(self.resign(records, "evaluability", mutation))
        with self.assertRaises(ValueError):
            self.dossier(records+[records[0]])

    def test_same_key_aliases_do_not_establish_independence(self):
        for role in review.OBLIGATIONS:
            self.keys[role] = self.keys["evaluability"]
            self.policy["reviewers"][role]["public_key"] = self.policy["reviewers"]["evaluability"]["public_key"]
        self.save_policy()
        record = intake.build_evidence(self.root, TRACK)
        self.assertEqual(self.dossier(record=record)["outcome"], "infra_failed")

    def test_supported_cost_discrepancy_requires_a_fatal_objection(self):
        records = self.signed_reviews()
        for field in ("time_log2", "memory_log2_bytes", "preprocessing_log2", "nonuniform_advice_log2_bytes"):
            with self.subTest(field=field):
                changed = self.resign(records, "cost", lambda b: b["reconstruction"].update(
                    {field: b["reconstruction"][field]+1}))
                with self.assertRaises(ValueError):
                    self.dossier(changed)
        changed = self.resign(records, "cost", lambda b: b["reconstruction"].update(success_probability=0.99))
        with self.assertRaises(ValueError):
            self.dossier(changed)

    def test_uncertain_cost_can_score_and_remains_visible(self):
        records = self.signed_reviews()
        def change(body):
            body["reconstruction"]["time_log2"] += 1
            next(x for x in body["obligations"] if x["id"] == "total_work")["status"] = "unresolved"
        dossier = self.dossier(self.resign(records, "cost", change))
        self.assertEqual(dossier["outcome"], "plausible_not_refuted")
        self.assertIn("cost/total_work", dossier["uncertainties"])

    def test_unresolved_obligation_is_not_refutation(self):
        records = self.resign(self.signed_reviews(), "cryptanalysis",
                             lambda b: b["obligations"][0].update(status="unresolved"))
        self.assertEqual(self.dossier(records)["outcome"], "plausible_not_refuted")

    def test_fatal_requires_defense_adjudication_and_preserves_all_records(self):
        records = self.finding()
        self.assertEqual(self.dossier(records)["outcome"], "infra_failed")
        confirmed = self.dossier(records, challenges=[self.challenge(records, "confirmed")])
        self.assertEqual(confirmed["outcome"], "refuted")
        dismissed = self.dossier(records, challenges=[self.challenge(records)])
        self.assertEqual(dismissed["outcome"], "plausible_not_refuted")
        self.assertEqual(dismissed["reviews"], records)
        self.assertEqual(len(dismissed["challenges"]), 1)

    def test_dismissal_without_explicit_discharge_and_unresolved_adjudication_block(self):
        records = self.finding()
        for challenge in (self.challenge(records, discharged=[]), self.challenge(records, "unresolved")):
            self.assertEqual(self.dossier(records, challenges=[challenge])["outcome"], "plausible_not_refuted")
        records = self.finding("unresolved")
        self.assertEqual(self.dossier(records)["outcome"], "plausible_not_refuted")
        with self.assertRaises(ValueError):
            self.dossier(records, challenges=[self.challenge(records, "confirmed")])

    def test_duplicate_unlinked_and_self_adjudication_rejected(self):
        records = self.finding()
        challenge = self.challenge(records)
        with self.assertRaises(ValueError):
            self.dossier(records, challenges=[challenge, challenge])
        for field, value in (("finding_id", "new-unchallenged-finding"), ("defense_sha256", "0"*64),
                             ("discharged_obligations", ["success"])):
            altered = copy.deepcopy(challenge)
            altered["adjudication"]["body"][field] = value
            altered["adjudication"] = review.sign(altered["adjudication"]["body"], self.keys["adjudicator"])
            with self.assertRaises(ValueError):
                self.dossier(records, challenges=[altered])

    def test_heuristics_require_both_roles_and_plausible_support(self):
        self.change("candidates/"+TRACK+"/claim.json", lambda v: v.update(heuristics=[{
            "id": "H1", "statement": "Synthetic fixture", "role": "success", "evidence": ["proof.md"],
            "scope": "fixture", "extrapolation": "fixture", "limitations": "fixture"}]))
        record = intake.build_evidence(self.root, TRACK)
        records = self.signed_reviews(record)
        self.assertEqual(self.dossier(records, record=record)["outcome"], "plausible_not_refuted")
        altered = self.resign(records, "experiments", lambda b: b["heuristics"][0].update(status="plausible"))
        self.assertEqual(self.dossier(altered, record=record)["outcome"], "plausible_not_refuted")
        unsupported=self.resign(records,"experiments",lambda b:b["heuristics"][0].update(status="unsupported"))
        self.assertEqual(self.dossier(unsupported,record=record)["outcome"],"not_evaluable")
        with self.assertRaises(ValueError):
            self.dossier(self.resign(records, "cryptanalysis", lambda b: b.update(heuristics=[])), record=record)

    def test_evaluability_gap_and_unsupported_heuristic_block_exploratory_scoring(self):
        records=self.resign(self.signed_reviews(), 'evaluability',
            lambda b:b['obligations'][0].update(status='unresolved'))
        self.assertEqual(self.dossier(records)['outcome'],'not_evaluable')
        with self.assertRaises(ValueError):review.score(self.record,self.dossier(records))

    def test_analysis_counts_are_bounded_and_do_not_assert_attack_success(self):
        self.assertEqual(experiments.analysis_output({'counts':[{'id':'H','tested':100,'satisfied':39}]}),
                         {'counts':[{'id':'H','tested':100,'satisfied':39}]})
        for count in ({'id':'H','tested':True,'satisfied':0}, {'id':'H','tested':100,'satisfied':101},
                      {'id':'H','tested':0,'satisfied':0}):
            with self.assertRaises(ValueError):experiments.analysis_output({'counts':[count]})

    def test_provider_transport_schema_provenance_and_no_tools(self):
        self.policy["provider"]["models"]["evaluability"] = "vendor/exact-model"
        self.save_policy()
        record = intake.build_evidence(self.root, TRACK)
        template = review.template(record, "evaluability", "evaluability")
        content = {k: template[k] for k in ("obligations", "heuristics", "findings", "reconstruction")}
        for obligation in content["obligations"]:
            for citation in obligation["citations"]:
                citation.pop("sha256", None)
        def transport(payload):
            self.assertNotIn("tools", payload)
            self.assertNotIn("api-key-fixture", common.canonical(payload).decode())
            self.assertTrue(payload["response_format"]["json_schema"]["strict"])
            return {"id": "synthetic-request", "model": "vendor/exact-model", "choices": [{
                "finish_reason": "stop", "message": {"content": json.dumps(content)}}]}
        result = provider.request_review(record, "evaluability", self.policy, "evaluability",
            self.keys["evaluability"], "api-key-fixture", transport=transport)
        self.assertEqual(result["body"]["provenance"]["request_id"], "synthetic-request")
        self.assertNotIn("api-key-fixture", common.canonical(result).decode())
        for reason in ("length", "tool_calls"):
            def bad(payload):
                result = transport(payload)
                result["choices"][0]["finish_reason"] = reason
                return result
            with self.assertRaises(ValueError):
                provider.request_review(record, "evaluability", self.policy, "evaluability",
                    self.keys["evaluability"], "fixture", transport=bad)

    def test_sandbox_constraints_and_mutable_image_rejection(self):
        image = "python@sha256:"+"a"*64
        command = experiments.docker_command(image, "/fixed/snapshot", "attack.py", "fixture", self.policy)
        for flag in ("--network=none", "--read-only", "--cap-drop=ALL", "--pull=never",
                     "--security-opt=no-new-privileges", "--pids-limit=64", "--user=65534:65534"):
            self.assertIn(flag, command)
        self.assertNotIn("--privileged", command)
        self.assertNotIn("--env", command)
        with self.assertRaises(ValueError):
            experiments.docker_command("python:latest", "/fixed", "attack.py", "fixture", self.policy)

    @unittest.skipUnless(os.environ.get("CURVESMASH_TEST_IMAGE"), "Pinned Docker test image not supplied")
    def test_real_container_network_credentials_readonly_and_organizer_verification(self):
        self.policy["experiment_image"] = os.environ["CURVESMASH_TEST_IMAGE"]
        self.save_policy()
        folder = self.root / "candidates" / TRACK
        # Trusted organizer fixture, executed only in the locked container.
        source = '''import json, os, socket, sys
assert not any(k in os.environ for k in ("OPENROUTER_API_KEY", "GITHUB_TOKEN"))
try:
    open("/candidate/proof.md", "w")
    raise AssertionError("candidate mount writable")
except OSError as error:
    assert error.errno in (13, 30)
try:
    socket.create_connection(("1.1.1.1", 443), timeout=1)
    raise AssertionError("network available")
except OSError:
    pass
assert set(json.loads(sys.stdin.readline())) == {"Q"}
print(json.dumps({"x": "0"*64}))
'''
        (folder / "fixture.py").write_text(source)
        self.change("candidates/"+TRACK+"/claim.json", lambda v: v.update(
            experiment={"entrypoint": "fixture.py", "trials": 1}))
        record = intake.build_evidence(self.root, TRACK)
        with patch("evaluator.verifier.secrets.randbelow", return_value=0), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "host-secret-fixture"}):
            report = experiments.run(record, self.policy, "execution", self.keys["execution"])
        self.assertTrue(report["body"]["results"][0]["valid"])
        self.assertNotIn("host-secret-fixture", common.canonical(report).decode())
        experiments.validate_report(report, record, self.policy)
        reviews = []
        for role in review.OBLIGATIONS:
            body = review.template(record, role, role, report)
            for item in body["obligations"]:
                item.update(status="supported", reason="Synthetic fixture only.")
            reviews.append(review.sign(body, self.keys[role]))
        dossier = review.aggregate(record, reviews, definition_approval=self.approval(record), experiment=report)
        self.assertEqual(dossier["outcome"], "plausible_not_refuted")
        altered = copy.deepcopy(report)
        altered["body"]["results"][0]["valid"] = False
        altered = review.sign(altered["body"], self.keys["execution"])
        with self.assertRaises(ValueError):
            experiments.validate_report(altered, record, self.policy)
        with self.assertRaises(ValueError):
            review.aggregate(record, reviews, definition_approval=self.approval(record), experiment=altered)

    @unittest.skipUnless(os.environ.get("CURVESMASH_TEST_IMAGE"), "Pinned Docker test image not supplied")
    def test_real_container_analysis_counts_are_not_production_attack_results(self):
        self.policy['experiment_image']=os.environ['CURVESMASH_TEST_IMAGE'];self.save_policy()
        folder=self.root/'candidates'/TRACK
        (folder/'counts.py').write_text('import json,sys\np=json.loads(sys.stdin.readline())\nassert set(p)=={"track","trial","seed"}\nprint(json.dumps({"counts":[{"id":"H","tested":100,"satisfied":39}]}))\n')
        self.change('candidates/'+TRACK+'/claim.json',lambda c:c.update(
            experiment={'entrypoint':'counts.py','trials':1,'kind':'analysis'}))
        record=intake.build_evidence(self.root,TRACK)
        report=experiments.run(record,self.policy,'execution',self.keys['execution'])
        experiments.validate_report(report,record,self.policy)
        self.assertIsNone(report['body']['results'][0]['valid'])
        bad=copy.deepcopy(report);bad['body']['results'][0]['valid']=True
        with self.assertRaises(ValueError):
            experiments.validate_report(review.sign(bad['body'],self.keys['execution']),record,self.policy)

    def test_bounded_process_timeout_and_output_flood(self):
        for code, timeout, limit in (("import time; time.sleep(5)", 0.1, 1024),
                                     ("print('a'*10000)", 5, 1024)):
            with self.assertRaises(ValueError):
                experiments.bounded_process([sys.executable, "-c", code], b"", timeout, limit)
        out, err = experiments.bounded_process([sys.executable, "-c", "print('{}')"], b"", 5, 1024)
        self.assertEqual(common.parse(out), {})

    def test_output_never_overwrites_or_follows_links(self):
        path = self.root / "result.json"
        common.write_new(path, {"fixture": True})
        with self.assertRaises(FileExistsError):
            common.write_new(path, {})
        linked = self.root / "linked"
        linked.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            common.write_new(linked / "new.json", {})

    def test_cli_end_to_end_and_stale_score_protection(self):
        evidence = self.root / "evidence.json"
        dossier = self.root / "dossier.json"
        common.write_new(evidence, self.record)
        common.write_new(dossier, self.dossier())
        command = [sys.executable, "-m", "evaluator.cli", "--root", str(self.root),
                   "score", "--evidence", str(evidence), "--dossier", str(dossier)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=10,
                                env={k:v for k,v in os.environ.items() if k != "OPENROUTER_API_KEY"})
        self.assertEqual(result.returncode, 0, result.stderr)
        score_path = self.root / ".yukon/scores" / (TRACK+".json")
        self.assertTrue(score_path.exists())
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        score_path.unlink()
        (self.root / "candidates" / TRACK / "README.md").write_text("Changed evidence")
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(score_path.exists())


if __name__ == "__main__":
    unittest.main()
