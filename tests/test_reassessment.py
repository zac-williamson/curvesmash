"""History changes cannot silently alter targets, algorithms or unchanged accepted scores."""
import copy,json,unittest,os,subprocess
from unittest.mock import patch
from tests import test_evaluator as fixtures
TRACK=fixtures.TRACK
from evaluator import common,intake,review,reassessment

class Reassessment(unittest.TestCase):
    setUp=fixtures.Evaluation.setUp
    save_policy=fixtures.Evaluation.save_policy
    signed_reviews=fixtures.Evaluation.signed_reviews
    dossier=fixtures.Evaluation.dossier
    approval=fixtures.Evaluation.approval
    def packet(self):
        return {'record':self.record,'dossier':self.dossier(),'history':[]}
    def current(self,packet,mutate=None):
        entry={'track':TRACK,'package_identity':reassessment.package_identity(packet['record']),
            'artifact_id':123,'artifact_sha256':'a'*64,'packet_sha256':common.digest(packet)}
        (self.root/'reorg/plan.json').write_text(json.dumps({'schema_version':1,'entries':[entry]}))
        if mutate:mutate()
        return intake.build_evidence(self.root,TRACK),entry
    def transport(self,decision='accepted',value=None):
        def send(payload):
            user=json.loads(payload['messages'][1]['content'])
            response={'decision':decision,'time_log2':user['previous_score'] if decision=='accepted' and value is None else value,
                'reason':'Synthetic organizer reassessment fixture only.'}
            return {'id':'fixture','model':self.policy['provider']['models']['cost'],'choices':[
                {'finish_reason':'stop','message':{'content':json.dumps(response)}}]}
        return send
    def test_preserves_unchanged_score_and_authenticated_history(self):
        packet=self.packet();record,entry=self.current(packet)
        signed=reassessment.request_reassessment(record,packet,self.policy,self.keys['cost'],'fixture',transport=self.transport())
        dossier=reassessment.reassessment_dossier(record,packet,signed,self.policy)
        self.assertEqual(dossier['score'],self.record['evidence']['claim']['claim']['time_log2'])
        self.assertTrue(dossier['scoring_policy_unchanged'])
        with self.assertRaises(ValueError):
            reassessment.request_reassessment(record,packet,self.policy,self.keys['cost'],'fixture',transport=self.transport(value=1))
    def test_rejected_and_missing_evidence_have_no_score(self):
        packet=self.packet();record,_=self.current(packet)
        for decision in ('rejected','needs_evidence'):
            signed=reassessment.request_reassessment(record,packet,self.policy,self.keys['cost'],'fixture',transport=self.transport(decision))
            dossier=reassessment.reassessment_dossier(record,packet,signed,self.policy)
            self.assertIsNone(dossier['score']);self.assertNotEqual(dossier['outcome'],'plausible_not_refuted')
    def test_altered_packet_target_or_algorithm_cannot_reuse_history(self):
        packet=self.packet();record,entry=self.current(packet)
        changed=copy.deepcopy(packet);changed['dossier']['score']=1
        with self.assertRaises(ValueError):reassessment.validate_history(changed,entry,record)
        (self.root/'candidates'/TRACK/'proof.md').write_text('Different attack')
        changed=intake.build_evidence(self.root,TRACK)
        self.assertIsNone(reassessment.entry_for(changed))
    def test_price_change_requires_revised_bound(self):
        packet=self.packet()
        def mutate():
            cost=self.root/intake.COST;model=common.read_json(cost)
            model['reference_operation_costs'][TRACK]*=2;cost.write_text(json.dumps(model))
            claim=self.root/'candidates'/TRACK/'claim.json';value=common.read_json(claim)
            value['cost_model_sha256']=common.sha(cost.read_bytes());claim.write_text(json.dumps(value))
        record,_=self.current(packet,mutate)
        signed=reassessment.request_reassessment(record,packet,self.policy,self.keys['cost'],'fixture',transport=self.transport(value=128))
        dossier=reassessment.reassessment_dossier(record,packet,signed,self.policy)
        self.assertFalse(dossier['scoring_policy_unchanged']);self.assertEqual(dossier['score'],128)
    def test_workflow_runs_and_scores_pinned_reassessment(self):
        from evaluator import workflow
        packet=self.packet();record,_=self.current(packet)
        for args in (('init','-q'),('config','user.name','Organizer fixture'),
                     ('config','user.email','fixture@example.invalid'),('add','.'),('commit','-qm','Fixture')):
            subprocess.run(['git','-C',str(self.root),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        head=subprocess.check_output(['git','-C',str(self.root),'rev-parse','HEAD'],text=True).strip()
        work=self.root/'work';out=self.root/'reviews';final=self.root/'qualification'
        with patch('evaluator.reassessment.fetch_history',return_value=packet):
            workflow.freeze_source(self.root,head,TRACK,work)
        keys={name:self.keys[name].hex() for name in workflow.ROLES}
        with patch.dict(os.environ,{'OPENROUTER_API_KEY':'fixture',
                'CURVESMASH_REVIEW_SIGNING_KEYS':json.dumps(keys)}), \
             patch('evaluator.provider.completion',side_effect=lambda config,model,messages,schema,key,transport=None,audit=None:
                ({'decision':'accepted','time_log2':packet['record']['evidence']['claim']['claim']['time_log2'],
                  'reason':'Synthetic workflow reassessment fixture.'},'fixture-request')):
            self.assertEqual(workflow.review_job(self.root,TRACK,work,out),0)
        self.assertEqual(workflow.score_job(self.root,TRACK,work,out,final),0)
        result=common.read_json(self.root/'.yukon/scores'/f'{TRACK}.json')
        self.assertEqual(result['rescoreMode'],'preserved')
        self.assertEqual(result['score'],packet['record']['evidence']['claim']['claim']['time_log2'])
