"""Separated Yukon intake, review and scoring jobs with immutable run artifacts."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .common import (ARTIFACT_BYTES, MAX_BYTES, canonical, digest, exact, parse, read_file,
                     read_json, relative, require, sha, write_new)
from .intake import build_evidence, check_evidence, POLICY, TRACKS
from .review import aggregate, OBLIGATIONS, score, sign, definitions_binding
from . import experiments, provider, reassessment

ROOT = Path(__file__).resolve().parents[1]
ROLES = (*OBLIGATIONS, "defender", "adjudicator", "execution")


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
             "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}).stdout


def commit(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value),
            "Full immutable source commit required")
    return value


def tree(root, ref):
    # Git objects are read as inert data; never check out participant hooks/code.
    entries = {}
    for entry in git(root, "ls-tree", "-rz", commit(ref)).split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split()
        path = path.decode("utf-8")
        relative(path)
        require(mode in ("100644", "100755") and kind == "blob", "Links/submodules refused")
        entries[path] = (mode, object_id)
    require(len(entries) <= 4096, "Source tree exceeds organizer limit")
    return entries


def freeze_source(root, source, track, work, source_root=None):
    source_root = source_root or root
    trusted = git(root, "rev-parse", "HEAD").decode().strip()
    original, submitted = tree(root, trusted), tree(source_root, source)
    prefix = "candidates/"+track+"/"
    for path in set(original) | set(submitted):
        require(path.startswith(prefix) or original.get(path) == submitted.get(path),
                "Submission changed a protected path or sibling track")
    with tempfile.TemporaryDirectory() as temp:
        candidate, total, count = Path(temp).resolve(), 0, 0
        for path, (_, object_id) in submitted.items():
            if not path.startswith(prefix):
                continue
            size = int(git(source_root, "cat-file", "-s", object_id))
            total += size
            count += 1
            require(total <= MAX_BYTES and count <= 128, "Candidate exceeds submission limits")
            data = git(source_root, "cat-file", "blob", object_id)
            dest = candidate / path.removeprefix(prefix)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        record = build_evidence(root, track, candidate)
    write_new(work / "evidence.json", record)
    provenance = {"schema_version": 1, "trusted_commit": trusted, "source_commit": source,
        "binding": record["binding"], "track": track,
        "candidate_sha256": digest({p: f for p, f in record["evidence"]["files"].items()
                                    if p.startswith("candidate/")}),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1")}
    write_new(work / "provenance.json", provenance)
    policy = parse(record["evidence"]["files"][POLICY]["text"])
    if record["evidence"]["experiment_required"]:
        image = policy["experiment_image"]
        require(image is not None, "Experiment image must be provisioned")
        subprocess.run(["docker", "pull", image], check=True, timeout=180,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        write_new(work / "execution-body.json", experiments.run(record, policy, "execution"))
    history = reassessment.fetch_history(record, os.environ.get("GH_TOKEN"))
    if history is not None:
        write_new(work / "history.json", history)
    write_new(work / "intake-status.json", {"state": "complete", "binding": record["binding"]})
    return provenance


def load(root, track, work):
    record = read_json(work / "evidence.json", ARTIFACT_BYTES)
    evidence = check_evidence(record)
    require(evidence["track"] == track, "Wrong track artifact")
    provenance = read_json(work / "provenance.json")
    exact(provenance, ("schema_version", "trusted_commit", "source_commit", "binding", "track",
                       "candidate_sha256", "workflow_run_id", "workflow_run_attempt"))
    require(provenance["schema_version"] == 1 and provenance["binding"] == record["binding"]
            and provenance["track"] == track, "Wrong source provenance")
    commit(provenance["source_commit"])
    require(provenance["trusted_commit"] == git(root, "rev-parse", "HEAD").decode().strip(),
            "Artifact belongs to a different organizer release")
    if os.environ.get("GITHUB_RUN_ID"):
        require(provenance["workflow_run_id"] == os.environ["GITHUB_RUN_ID"] and
            provenance["workflow_run_attempt"] == os.environ["GITHUB_RUN_ATTEMPT"],
            "Cross-run or cross-attempt artifact refused")
    candidate_files = {p: f for p, f in evidence["files"].items() if p.startswith("candidate/")}
    require(provenance["candidate_sha256"] == digest(candidate_files), "Wrong candidate provenance")
    with tempfile.TemporaryDirectory() as temp:
        candidate = Path(temp).resolve()
        for path, file in candidate_files.items():
            dest = candidate / path.removeprefix("candidate/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(file["text"], encoding="utf-8")
        require(build_evidence(root, track, candidate) == record,
                "Evidence differs from the trusted release")
    return record, parse(evidence["files"][POLICY]["text"])


def service_keys(policy):
    keys = parse(os.environ.get("CURVESMASH_REVIEW_SIGNING_KEYS", "{}"))
    exact(keys, ROLES)
    result = {}
    for role in ROLES:
        require(type(keys[role]) is str and re.fullmatch(r"[0-9a-f]{64}", keys[role]),
                "Invalid service key encoding")
        private = bytes.fromhex(keys[role])
        public = Ed25519PrivateKey.from_private_bytes(private).public_key().public_bytes_raw().hex()
        require(policy["reviewers"][role] == {"public_key": public, "roles": [role]},
                "Service key does not match the protected policy")
        result[role] = private
    return result


def review_job(root, track, work, output):
    record, policy = load(root, track, work)
    errors, reviews, challenges, provenance = [], [], [], []
    experiment = None
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        require(bool(api_key), "OPENROUTER_API_KEY missing")
        keys = service_keys(policy)
        require(set(policy["provider"]["models"]) == set(ROLES)-{"execution"},
                "Review model roles not provisioned")
        if record["evidence"]["experiment_required"]:
            body = read_json(work / "execution-body.json")
            experiments.validate_body(body, record, policy)
            experiment = sign(body, keys["execution"])
            experiments.validate_report(experiment, record, policy)
            write_new(output / "experiment.json", experiment)
        if reassessment.entry_for(record) is not None:
            history = read_json(work / "history.json", reassessment.MAX_HISTORY)
            decision = reassessment.request_reassessment(record, history, policy, keys['cost'], api_key,
                audit=lambda attempt: write_new(output / 'reassessment-attempt.json', attempt), experiment=experiment)
            dossier = reassessment.reassessment_dossier(record, history, decision, policy, experiment)
            write_new(output / 'reassessment.json', decision)
            write_new(output / 'history.json', history)
            write_new(output / 'packet.json', {'record':record,'dossier':dossier,
                'history':history['history']+[history['dossier']]})
            write_new(output / 'review-status.json', {'binding':record['binding'],'errors':[],
                'review_count':0,'challenge_count':0,'challenge_provenance':[]})
            return 0
        # Independent initial calls. No earlier verdict appears in a later prompt.
        for role in OBLIGATIONS:
            try:
                result = provider.request_review(record, role, policy, role, keys[role], api_key, experiment,
                    audit=lambda attempt, role=role: write_new(output / (role+"-attempt.json"), attempt))
                write_new(output / (role+".json"), result)
                reviews.append(result)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                errors.append({"stage": role, "error": type(exc).__name__})
        findings = [(r, f) for r in reviews for f in r["body"]["findings"] if f["severity"] == "fatal"]
        require(len(findings) <= 16, "Challenge call budget exceeded; owner follow-up required")
        for index, (review, finding) in enumerate(findings):
            try:
                defense, meta = provider.request_challenge(record, review, finding, "defender", policy,
                    keys["defender"], api_key, experiment=experiment,
                    audit=lambda attempt, index=index: write_new(output / (f"defense-{index}-attempt.json"), attempt))
                write_new(output / (f"defense-{index}.json"), defense)
                provenance.append(meta)
                adjudication, meta = provider.request_challenge(record, review, finding, "adjudicator",
                    policy, keys["adjudicator"], api_key, defense, experiment,
                    audit=lambda attempt, index=index: write_new(output / (f"adjudication-{index}-attempt.json"), attempt))
                challenge = {"defense": defense, "adjudication": adjudication}
                # Validate the exact link, identity separation and obligation discharge.
                aggregate(record, reviews, [challenge], experiment=experiment)
                write_new(output / (f"challenge-{index}.json"), challenge)
                challenges.append(challenge)
                provenance.append(meta)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                errors.append({"stage": "challenge-"+str(index), "error": type(exc).__name__})
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Names of missing configuration are safe; never preserve exception bodies/credentials.
        code = "missing_provider_key" if not os.environ.get("OPENROUTER_API_KEY") else "review_configuration_or_protocol"
        errors.append({"stage": "provisioning", "error": type(exc).__name__, "code": code})
    packet_dossier=aggregate(record, reviews, challenges, experiment=experiment)
    packet_dossier['scoring_policy']=reassessment.scoring_policy(record)
    packet_dossier['score']=record['evidence']['claim']['claim']['time_log2'] if packet_dossier['outcome']=='plausible_not_refuted' and not errors else None
    write_new(output / 'packet.json', {'record':record,'dossier':packet_dossier, 'history':[]})
    write_new(output / "review-status.json", {"binding": record["binding"], "errors": errors,
        "review_count": len(reviews), "challenge_count": len(challenges), "challenge_provenance": provenance})
    return 1 if errors else 0


def score_job(root, track, work, reviews_dir, output, destination=None):
    require(not os.environ.get("OPENROUTER_API_KEY") and
            not os.environ.get("CURVESMASH_REVIEW_SIGNING_KEYS"), "Scoring must be credential-free")
    record, policy = load(root, track, work)
    status = read_json(reviews_dir / "review-status.json")
    require(status["binding"] == record["binding"], "Review status bound to another submission")
    reviews = [read_json(reviews_dir / (r+".json")) for r in OBLIGATIONS
               if (reviews_dir / (r+".json")).exists()]
    challenges = [read_json(p) for p in sorted(reviews_dir.glob("challenge-*.json"))]
    require(status["review_count"] == len(reviews) and status["challenge_count"] == len(challenges),
            "Incomplete review artifact")
    experiment = read_json(reviews_dir / "experiment.json") if record["evidence"]["experiment_required"] else None
    if reassessment.entry_for(record) is not None:
        history = read_json(reviews_dir / 'history.json', reassessment.MAX_HISTORY)
        dossier = reassessment.reassessment_dossier(record, history,
            read_json(reviews_dir / 'reassessment.json'), policy, experiment)
    else:
        require(not (reviews_dir / 'reassessment.json').exists(), 'Unpinned reassessment refused')
        dossier = aggregate(record, reviews, challenges, experiment=experiment)
    write_new(output / "dossier.json", dossier)
    write_new(output / "qualification.json", {"binding": record["binding"], "outcome": dossier["outcome"],
        "infrastructure_errors": status["errors"], "definition_binding": definitions_binding(record["evidence"]),
        "review_run_id": os.environ.get("CURVESMASH_REVIEW_RUN_ID", os.environ.get("GITHUB_RUN_ID", "local")),
        "provenance": read_json(work / "provenance.json"), "dossier_sha256": digest(dossier)})
    print(dossier["outcome"]+": "+str(len(dossier["blockers"]))+" outstanding gates.")
    if status["errors"]:
        print("Review infrastructure incomplete; no score emitted.")
        return 1
    if dossier["outcome"] != "plausible_not_refuted":
        return 2
    if 'reassessment' in dossier:
        bounds = record['evidence']['claim']['claim']
        result = {'score':dossier['score'],'timeLog2':dossier['score'],'binding':record['binding'],
            'dossier_sha256':digest(dossier),'track':track,'claim_kind':dossier['claim_kind'],
            'memoryLog2Bytes':bounds['memory_log2_bytes'],'promotionMode':'manual',
            'policy':dossier['policy'],'timeUnit':bounds['time_unit'],
            'rescoreMode':'preserved' if dossier['scoring_policy_unchanged'] else 'revised',
            'previous_packet_sha256':dossier['previous_packet_sha256']}
    else:
        result = score(record, dossier)
    score_path = ".yukon/scores/"+track+".json"
    write_new(root / score_path, result)
    if destination is not None:
        require(not destination.exists(), "Score staging directory must be fresh")
        # Preserve the exact manifest-relative path inside Yukon's named artifact.
        write_new(destination / score_path, result)
    print("Qualified score emitted; promotion remains manual.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("intake", "review", "score"))
    parser.add_argument("--track", choices=TRACKS, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--source")
    parser.add_argument("--source-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "intake":
            require(not os.environ.get("OPENROUTER_API_KEY") and
                    not os.environ.get("CURVESMASH_REVIEW_SIGNING_KEYS"), "Intake must be credential-free")
            source = commit(args.source or git(ROOT, "rev-parse", "HEAD").decode().strip())
            freeze_source(ROOT, source, args.track, args.work, args.source_root)
            print("Candidate frozen; credential-free intake complete.")
            return 0
        if args.command == "review":
            return review_job(ROOT, args.track, args.work, args.output or args.work / "reviews")
        return score_job(ROOT, args.track, args.work, args.reviews or args.work / "reviews",
                         args.output or args.work / "qualification", args.destination)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        if args.command == "intake":
            write_new(args.work / "intake-failure.json", {"track": args.track,
                "stage": "intake", "code": "source_or_execution_validation_failed"})
        print("Execution refused: configuration, provenance or artifact validation failed; no score emitted.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
