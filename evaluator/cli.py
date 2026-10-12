"""Organizer commands; intake and score stages require no provider secrets."""
import argparse
import os
from pathlib import Path
import sys

from .common import read_json, read_file, write_new, require, parse, ARTIFACT_BYTES
from .intake import build_evidence, check_evidence, TRACKS, POLICY
from .review import OBLIGATIONS, template, sign, aggregate, score

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT,
                        help="Trusted organizer checkout, never a participant checkout")
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--track", required=True, choices=TRACKS)
    prepare.add_argument("--candidate", type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    for name in ("template", "review", "experiment", "qualify", "score"):
        command = sub.add_parser(name)
        command.add_argument("--evidence", required=True, type=Path)
        command.add_argument("--candidate", type=Path)
        if name != "score":
            command.add_argument("--output", required=True, type=Path)
        if name in ("template", "review", "experiment"):
            command.add_argument("--reviewer", required=True)
        if name in ("template", "review"):
            command.add_argument("--role", required=True, choices=OBLIGATIONS)
        if name in ("review", "experiment"):
            command.add_argument("--key", required=True, type=Path,
                                 help="32-byte raw Ed25519 service key outside the submission")
        if name != "experiment":
            command.add_argument("--experiment", type=Path)
        if name == "qualify":
            command.add_argument("--reviews", type=Path, nargs="*", default=[])
            command.add_argument("--challenges", type=Path, nargs="*", default=[])
            command.add_argument("--definition-approval", type=Path)
        if name == "score":
            command.add_argument("--dossier", required=True, type=Path)
    signing = sub.add_parser("sign")
    signing.add_argument("--body", required=True, type=Path)
    signing.add_argument("--key", required=True, type=Path)
    signing.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "sign":
            write_new(args.output, sign(read_json(args.body), read_file(args.key, 32)))
            return 0
        if args.command == "prepare":
            record = build_evidence(args.root, args.track, args.candidate)
            write_new(args.output, record)
            print("Submission frozen for review; no score emitted.")
            return 0
        record = read_json(args.evidence, ARTIFACT_BYTES)
        evidence = check_evidence(record)
        # Artifact contents, self-reported outcomes and participant policy files are never authority.
        require(build_evidence(args.root, evidence["track"], args.candidate) == record,
                "Evidence differs from current trusted definitions or candidate bytes")
        policy = parse(evidence["files"][POLICY]["text"])
        experiment = read_json(args.experiment) if getattr(args, "experiment", None) else None
        if args.command == "template":
            write_new(args.output, template(record, args.role, args.reviewer, experiment))
        elif args.command == "review":
            from .provider import request_review
            result = request_review(record, args.role, policy, args.reviewer,
                                    read_file(args.key, 32), os.environ.get("OPENROUTER_API_KEY"), experiment)
            write_new(args.output, result)
        elif args.command == "experiment":
            from .experiments import run
            write_new(args.output, run(record, policy, args.reviewer, read_file(args.key, 32)))
        elif args.command == "qualify":
            dossier = aggregate(record, [read_json(p) for p in args.reviews],
                [read_json(p) for p in args.challenges],
                read_json(args.definition_approval) if args.definition_approval else None, experiment)
            write_new(args.output, dossier)
            print(dossier["outcome"]+": "+str(len(dossier["blockers"]))+" outstanding gates; no score emitted.")
            return 0 if dossier["outcome"] == "qualified" else 2
        elif args.command == "score":
            require(not os.environ.get("OPENROUTER_API_KEY"), "Scoring must run without provider credentials")
            result = score(record, read_json(args.dossier))
            write_new(args.root / ".yukon/scores" / (evidence["track"]+".json"), result)
            print("Qualified complexity score emitted; promotion remains manual.")
        return 0
    except (ValueError, KeyError, TypeError, OSError, RecursionError, UnicodeError) as exc:
        # Avoid echoing arbitrary candidate/provider content or sensitive file locations.
        print("Evaluation refused: "+type(exc).__name__+". See the documented contract and supplied artifact.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
