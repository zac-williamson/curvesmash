#!/usr/bin/env python3
"""Provision service signing identities; never create scientific approval receipts."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from evaluator.common import canonical, parse, read_file, require
from evaluator.workflow import ROLES


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--key-directory', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = args.key_directory.absolute()
    require(not directory.is_relative_to(root), 'Signing keys must stay outside the repository')
    for parent in (directory, *directory.parents):
        require(not parent.is_symlink(), 'Symlinked key directory refused')
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    bundle = directory / 'review-keys.json'
    definition_key = directory / 'definitions.key'
    if bundle.exists():
        require(bundle.stat().st_mode & 0o077 == 0, 'Private key file must have mode 600')
        keys = parse(read_file(bundle))
        require(set(keys) == set(ROLES), 'Existing key bundle has wrong roles')
    else:
        keys = {role: Ed25519PrivateKey.generate().private_bytes_raw().hex() for role in ROLES}
        fd = os.open(bundle, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(keys)+b'\n')
    if definition_key.exists():
        require(definition_key.stat().st_mode & 0o077 == 0, 'Private key file must have mode 600')
        definitions = read_file(definition_key, 32)
    else:
        definitions = Ed25519PrivateKey.generate().private_bytes_raw()
        fd = os.open(definition_key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(definitions)
    policy_file = root / 'evaluation/policy-v1.json'
    policy = parse(read_file(policy_file))
    policy['reviewers'] = {role: {'roles': [role], 'public_key': Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(keys[role])).public_key().public_bytes_raw().hex()} for role in ROLES}
    policy['definition_approvers'] = {'definitions': {'roles': ['definitions'], 'public_key':
        Ed25519PrivateKey.from_private_bytes(definitions).public_key().public_bytes_raw().hex()}}
    policy['provider']['models'] = {role: 'openai/gpt-5.6-sol' for role in ROLES if role != 'execution'}
    policy['provider']['timeout_seconds'] = 600
    policy['provider']['max_tokens'] = 16000
    policy['experiment_image'] = 'python@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1'
    policy_file.write_text(json.dumps(policy, indent=2)+'\n')
    print('Seven service identities and a separate organizer approval identity provisioned. No approval issued.')


if __name__ == '__main__':
    main()
