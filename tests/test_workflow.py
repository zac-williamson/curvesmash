"""Trust-boundary and real stage-contract tests; all scientific receipts are fixtures."""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from evaluator import common, intake, review, workflow, provider
import test_evaluator as fixtures
TRACK = fixtures.TRACK


class Workflow(unittest.TestCase):
    setUp = fixtures.Evaluation.setUp
    save_policy = fixtures.Evaluation.save_policy
    signed_reviews = fixtures.Evaluation.signed_reviews
    approval = fixtures.Evaluation.approval
    resign = fixtures.Evaluation.resign
    finding = fixtures.Evaluation.finding
    challenge = fixtures.Evaluation.challenge

    def initialize(self):
        self.work = Path(self.temp.name).resolve() / 'intake'
        self.output = Path(self.temp.name).resolve() / 'reviews'
        self.result = Path(self.temp.name).resolve() / 'qualification'
        self.keys_env = {'CURVESMASH_REVIEW_SIGNING_KEYS': json.dumps(
            {role: self.keys[role].hex() for role in workflow.ROLES}), 'OPENROUTER_API_KEY': 'fixture-key'}
        self.policy['provider']['models'] = {role: 'vendor/exact-model' for role in workflow.ROLES
                                            if role != 'execution'}
        self.save_policy()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.git('add', '.')
        self.git('-c', 'user.email=fixture@example.invalid', '-c', 'user.name=Fixture', 'commit', '-qm', 'Fixture')
        self.source = self.git('rev-parse', 'HEAD').decode().strip()
        workflow.freeze_source(self.root, self.source, TRACK, self.work)
        self.record = workflow.load(self.root, TRACK, self.work)[0]

    def git(self, *args):
        return workflow.git(self.root, *args)

    def provider_fixture(self, record, role, policy, identity, key, api_key, experiment, audit=None):
        self.assertEqual(record, self.record)
        self.assertEqual(api_key, 'fixture-key')
        # The submitted algorithm stays inert even while provider credentials exist.
        return next(r for r in self.signed_reviews(record) if r['body']['role'] == role)

    def run_reviews(self):
        with patch.dict(os.environ, self.keys_env), patch.object(provider, 'request_review', self.provider_fixture):
            return workflow.review_job(self.root, TRACK, self.work, self.output)

    def test_separated_stages_emit_exact_yukon_path_and_numeric_score(self):
        self.initialize()
        self.assertEqual(self.run_reviews(), 0)
        destination = Path(self.temp.name).resolve() / 'yukon-score'
        with patch.dict(os.environ, {'CURVESMASH_DEFINITION_APPROVAL': json.dumps(self.approval())}, clear=True):
            self.assertEqual(workflow.score_job(self.root, TRACK, self.work, self.output, self.result, destination), 0)
        staged = common.read_json(destination / '.yukon/scores' / (TRACK+'.json'))
        self.assertEqual(staged['score'], staged['timeLog2'])
        self.assertEqual(staged['binding'], self.record['binding'])
        self.assertEqual(staged['promotionMode'], 'manual')
        with self.assertRaises(FileExistsError), patch.dict(os.environ, {}, clear=True):
            workflow.score_job(self.root, TRACK, self.work, self.output, self.result, destination)

    def test_missing_provider_produces_honest_pending_dossier_without_score(self):
        self.initialize()
        with patch.dict(os.environ, {}, clear=True), patch.object(provider, 'request_review') as call:
            self.assertEqual(workflow.review_job(self.root, TRACK, self.work, self.output), 1)
            call.assert_not_called()
            self.assertEqual(workflow.score_job(self.root, TRACK, self.work, self.output, self.result), 1)
        report = common.read_json(self.result / 'qualification.json')
        self.assertEqual(report['outcome'], 'pending_review')
        self.assertEqual(report['infrastructure_errors'][0]['code'], 'missing_provider_key')
        self.assertFalse((self.root / '.yukon/scores').exists())

    def test_live_reviews_cannot_substitute_for_definition_approval(self):
        self.initialize()
        self.run_reviews()
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(workflow.score_job(self.root, TRACK, self.work, self.output, self.result), 2)
        self.assertIn('Protected definitions/evaluator lack scientific approval',
                      common.read_json(self.result / 'dossier.json')['blockers'])
        self.assertFalse((self.root / '.yukon/scores').exists())

    def test_protected_changes_sibling_changes_and_symlinks_refused(self):
        self.initialize()
        for path in ('evaluator/provider.py', 'candidates/'+intake.TRACKS[1]+'/README.md'):
            self.git('checkout', self.source, '--', '.')
            (self.root / path).write_text('untrusted replacement')
            self.git('add', '.')
            self.git('-c', 'user.email=fixture@example.invalid', '-c', 'user.name=Fixture', 'commit', '-qm', 'Attack')
            candidate = self.git('rev-parse', 'HEAD').decode().strip()
            self.git('checkout', '--detach', self.source)
            with self.assertRaises(ValueError):
                workflow.freeze_source(self.root, candidate, TRACK, Path(self.temp.name).resolve()/'refused')
        link = self.root / 'candidates'/TRACK/'link'
        link.symlink_to('/etc/passwd')
        self.git('add', '.')
        self.git('-c', 'user.email=fixture@example.invalid', '-c', 'user.name=Fixture', 'commit', '-qm', 'Link')
        with self.assertRaises(ValueError):
            workflow.freeze_source(self.root, self.git('rev-parse','HEAD').decode().strip(), TRACK,
                                   Path(self.temp.name).resolve()/'refused')

    def test_candidate_only_commit_is_data_and_cannot_execute(self):
        self.initialize()
        path = self.root / 'candidates'/TRACK/'attack.py'
        marker = Path(self.temp.name).resolve()/'executed'
        path.write_text("raise RuntimeError('untrusted code')\n")
        self.git('add', '.')
        self.git('-c', 'user.email=fixture@example.invalid', '-c', 'user.name=Fixture', 'commit', '-qm', 'Candidate')
        candidate = self.git('rev-parse','HEAD').decode().strip()
        self.git('checkout', '--detach', self.source)
        work = Path(self.temp.name).resolve()/'candidate'
        workflow.freeze_source(self.root, candidate, TRACK, work)
        self.assertIn('candidate/attack.py', workflow.load(self.root, TRACK, work)[0]['evidence']['files'])
        self.assertFalse(marker.exists())

    def test_artifact_tampering_cross_run_and_score_credentials_refused(self):
        self.initialize()
        with patch.dict(os.environ, {'GITHUB_RUN_ID': 'different-run', 'GITHUB_RUN_ATTEMPT': '1'}):
            with self.assertRaises(ValueError):
                workflow.load(self.root, TRACK, self.work)
        self.run_reviews()
        for credential in ('OPENROUTER_API_KEY', 'CURVESMASH_REVIEW_SIGNING_KEYS'):
            with patch.dict(os.environ, {credential: 'fixture'}), self.assertRaises(ValueError):
                workflow.score_job(self.root, TRACK, self.work, self.output, self.result)
        provenance = common.read_json(self.work/'provenance.json')
        provenance['candidate_sha256'] = '0'*64
        (self.work/'provenance.json').write_text(json.dumps(provenance))
        with self.assertRaises(ValueError):
            workflow.load(self.root, TRACK, self.work)

    def test_challenge_transport_authenticates_exact_objection_and_provenance(self):
        self.initialize()
        records = self.finding()
        original = next(r for r in records if r['body']['role']=='cryptanalysis')
        finding = original['body']['findings'][0]
        def transport(payload):
            self.assertNotIn('fixture-key', common.canonical(payload).decode())
            content = {'reason': 'Synthetic defense fixture only.', 'citations': finding['citations']}
            if 'Adjudicate' in payload['messages'][0]['content']:
                content.update(decision='dismissed', discharged_obligations=['correctness'])
            return {'model':'vendor/exact-model','id':'fixture-request','choices':[{
                'finish_reason':'stop','message':{'content':json.dumps(content)}}]}
        defense, meta = provider.request_challenge(self.record, original, finding, 'defender', self.policy,
            self.keys['defender'], 'fixture-key', transport=transport)
        adjudication, _ = provider.request_challenge(self.record, original, finding, 'adjudicator', self.policy,
            self.keys['adjudicator'], 'fixture-key', defense, transport=transport)
        dossier = review.aggregate(self.record, records, [{'defense':defense,'adjudication':adjudication}],
                                   self.approval())
        self.assertEqual(dossier['outcome'], 'qualified')
        self.assertEqual(meta['record_sha256'], common.digest(defense))
        self.assertEqual(meta['model'], 'vendor/exact-model')


if __name__ == '__main__':
    unittest.main()
