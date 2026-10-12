#!/usr/bin/env python3
"""Verify a GitHub review artifact and propose, but never install, a reassessment pin."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluator.common import canonical,digest,parse,read_file,require,sha,write_new
from evaluator.intake import build_evidence
from evaluator.reassessment import package_identity,validate_history,REPOSITORY,MAX_HISTORY
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive',required=True,type=Path);p.add_argument('--artifact-id',required=True,type=int)
a=p.parse_args()
try:
 metadata=parse(subprocess.run(['gh','api',f'repos/{REPOSITORY}/actions/artifacts/{a.artifact_id}'],
    check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30).stdout)
 data=read_file(a.archive,16*1024*1024)
 require(metadata['digest']=='sha256:'+sha(data),'Artifact differs from GitHub metadata')
 with zipfile.ZipFile(BytesIO(data)) as z:
    require(z.namelist().count('packet.json')==1 and z.getinfo('packet.json').file_size<=MAX_HISTORY,
        'Missing bounded history packet')
    packet=parse(z.read('packet.json'),MAX_HISTORY)
 track=packet['record']['evidence']['track'];record=build_evidence(ROOT,track)
 entry={'track':track,'package_identity':package_identity(packet['record']),
    'artifact_id':a.artifact_id,'artifact_sha256':sha(data),'packet_sha256':digest(packet)}
 validate_history(packet,entry,record)
 cache=ROOT/'.yukon/reports/history'/(digest(packet)+'.json')
 if cache.exists():require(read_file(cache).strip()==canonical(packet),'Cache collision')
 else:write_new(cache,packet)
 print(canonical(entry).decode())
except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError):
 print('History artifact verification failed.',file=sys.stderr);sys.exit(1)
