#!/usr/bin/env python3
"""Trusted-operator local pipeline. Solvers use local_tracks.py and remote Yukon judging."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluator.common import digest, parse, read_json, require, write_new
from evaluator.intake import build_evidence, POLICY, TRACKS
from evaluator import experiments, reassessment, workflow
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--track',required=True,choices=TRACKS)
    parser.add_argument('--stage',choices=('intake','review','score'))
    parser.add_argument('--work',type=Path)
    args=parser.parse_args()
    if args.stage is None:
        require(os.environ.get('OPENROUTER_API_KEY') and os.environ.get('CURVESMASH_REVIEW_SIGNING_KEYS'),
                'Local judging requires organizer credentials. Solvers use local_tracks.py check and submit to Yukon.')
        work=ROOT/'.yukon/reports/local'/uuid.uuid4().hex
        # Separate processes receive only their required credentials. Participant code runs
        # solely in the bounded container; local scores do not replace remote qualification.
        basic={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','DOCKER_HOST','DOCKER_CONTEXT')}
        for stage in ('intake','review','score'):
            env=dict(basic)
            if stage=='intake' and os.environ.get('GH_TOKEN'):env['GH_TOKEN']=os.environ['GH_TOKEN']
            if stage=='review':
                env.update({k:os.environ[k] for k in ('OPENROUTER_API_KEY','CURVESMASH_REVIEW_SIGNING_KEYS')})
            result=subprocess.run([sys.executable,__file__,'--track',args.track,'--stage',stage,'--work',str(work)],
                cwd=ROOT,env=env,check=False)
            if result.returncode:return result.returncode
        print('Local review artifacts:',work);return 0
    require(args.work is not None,'Missing stage work directory')
    intake=args.work/'intake';reviews=args.work/'reviews';output=args.work/'qualification'
    if args.stage=='intake':
        require(not os.environ.get('OPENROUTER_API_KEY') and not os.environ.get('CURVESMASH_REVIEW_SIGNING_KEYS'),
                'Intake must not receive review credentials')
        record=build_evidence(ROOT,args.track)
        head=workflow.git(ROOT,'rev-parse','HEAD').decode().strip()
        write_new(intake/'evidence.json',record)
        write_new(intake/'provenance.json',{'schema_version':1,'trusted_commit':head,'source_commit':head,
            'track':args.track,'binding':record['binding'],'candidate_sha256':digest({p:f for p,f in
            record['evidence']['files'].items() if p.startswith('candidate/')}),
            'workflow_run_id':'local','workflow_run_attempt':'1'})
        policy=parse(record['evidence']['files'][POLICY]['text'])
        if record['evidence']['experiment_required']:
            write_new(intake/'execution-body.json',experiments.run(record,policy,'execution'))
        history=reassessment.fetch_history(record,os.environ.get('GH_TOKEN'))
        if history is not None:write_new(intake/'history.json',history)
        return 0
    if args.stage=='review':return workflow.review_job(ROOT,args.track,intake,reviews)
    return workflow.score_job(ROOT,args.track,intake,reviews,output)

if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(str(error) if isinstance(error,ValueError) and str(error).startswith('Local judging') else
              'Local pipeline refused: '+type(error).__name__,file=sys.stderr);sys.exit(1)
