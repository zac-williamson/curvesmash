"""Freeze all submitted bytes and definitions before any review."""
from decimal import Decimal, localcontext, ROUND_CEILING
import importlib.metadata
import os
from pathlib import Path

from .common import (MAX_BYTES, HEX, exact, text, number, integer, decimal_integer,
                     relative, parse, read_file, read_json, digest, sha, require)

TRACKS = ("secp256k1-ecdlp", "bls12-381-invert-g1")
PROFILE = "target-profiles/production-v2.json"
COST = "cost-models/classical-group-work-v2.json"
POLICY = "evaluation/policy-v2.json"


def snapshot(directory):
    directory = Path(directory).absolute()
    require(directory.is_dir() and not directory.is_symlink(), "Invalid candidate directory")
    files, total, directories = {}, 0, 0
    for base, dirs, names in os.walk(directory, followlinks=False):
        directories += 1
        require(directories <= 128 and len(Path(base).relative_to(directory).parts) <= 8,
                "Candidate directory limit exceeded")
        for name in sorted(dirs + names):
            path = Path(base) / name
            relative(path.relative_to(directory).as_posix())
            require(not path.is_symlink(), "Candidate links are forbidden")
        for name in sorted(names):
            path = Path(base) / name
            data = read_file(path, MAX_BYTES-total)
            total += len(data)
            require(len(files) < 128, "Candidate file count limit exceeded")
            content = data.decode("utf-8")
            require("\x00" not in content, "Candidate text contains NUL")
            files["candidate/" + path.relative_to(directory).as_posix()] = {
                "sha256": sha(data), "text": content}
    require(files, "Empty submission")
    return dict(sorted(files.items()))


def log2_upper(value):
    integer(value, 1, 10**512)
    with localcontext() as ctx:
        # Inputs may have 512 decimal digits. Resolve even 2^1700+1 above the integer boundary.
        ctx.prec = 600
        result = Decimal(value).ln() / Decimal(2).ln()
        return float(result.quantize(Decimal("0.000001"), rounding=ROUND_CEILING))


def close_log(reported, bound):
    number(reported)
    require(reported == log2_upper(max(1, bound)), "Logarithm must be organizer-rounded log2 bound")


def validate_claim(files, track, profiles, cost, allow_draft=False):
    require("candidate/claim.json" in files, "Missing claim.json")
    claim = parse(files["candidate/claim.json"]["text"])
    keys = {"schema_version", "target_profile", "target_id", "cost_model",
            "target_profile_sha256", "cost_model_sha256", "submission_state",
            "review_status", "baseline_kind", "algorithm", "proof",
            "claim", "heuristics", "limitations", "lane"}
    require(type(claim) is dict and keys <= set(claim) <= keys | {"experiment"},
            "Claim has missing or unexpected fields")
    require(type(claim["schema_version"]) is int and claim["schema_version"] == 2,
            "Wrong claim schema")
    require(claim["submission_state"] in (("draft", "ready") if allow_draft else ("ready",)) and claim["review_status"] == "pending",
            "Candidate must be ready; candidate cannot assert review acceptance")
    require(claim["target_id"] == track and claim["target_profile"] == "production-v2"
            and claim["cost_model"] == "classical-group-work-v2", "Wrong target or cost model")
    for key, path in (("target_profile_sha256", PROFILE), ("cost_model_sha256", COST)):
        require(claim[key] == files[path]["sha256"], "Stale definition binding")
    require(claim["lane"] == "exploratory", "Only the exploratory policy is registered")
    for key in ("proof",):
        relative(claim[key])
        require("candidate/"+claim[key] in files, "Missing evidence reference")
    require(claim["baseline_kind"] in ("generic-accounting-control", "research-claim"),
            "Invalid claim kind")
    text(claim["algorithm"], 256)
    require(type(claim["limitations"]) is list and len(claim["limitations"]) <= 64,
            "Invalid limitations")
    for item in claim["limitations"]:
        text(item)
    bounds = claim["claim"]
    exact(bounds, ("time_log2", "time_unit", "memory_log2_bytes", "preprocessing_log2",
                   "success_probability", "nonuniform_advice_log2_bytes"))
    require(bounds["time_unit"] == "target-group-operations", "Wrong work unit")
    for field in ("time_log2", "memory_log2_bytes", "preprocessing_log2",
                  "nonuniform_advice_log2_bytes"):
        number(bounds[field], 0, 2048)
    number(bounds["success_probability"], cost["success_probability_minimum"], 1)
    require(bounds["nonuniform_advice_log2_bytes"] <= bounds["memory_log2_bytes"] <= 261,
            "Storage exceeds declared peak or RAM address space")
    # Cost arithmetic and scientific support are reviewed from the written argument.
    # Detailed kernel bounds are reviewed, not executed or accepted by this sum check.
    require(type(claim["heuristics"]) is list and len(claim["heuristics"]) <= 64,
            "Invalid heuristics")
    ids = set()
    for heuristic in claim["heuristics"]:
        exact(heuristic, ("id", "statement", "role", "evidence", "scope",
                          "extrapolation", "limitations"))
        for field in ("id", "statement", "role", "scope", "extrapolation", "limitations"):
            text(heuristic[field])
        require(heuristic["id"] not in ids, "Duplicate heuristic ID")
        ids.add(heuristic["id"])
        require(type(heuristic["evidence"]) is list and heuristic["evidence"],
                "Heuristic needs evidence references")
        for ref in heuristic["evidence"]:
            relative(ref)
            require("candidate/"+ref in files, "Missing heuristic evidence")
    if "experiment" in claim:
        require(set(claim["experiment"]) in ({"entrypoint", "trials"}, {"entrypoint", "trials", "kind"}), "Invalid experiment fields")
        require(claim["experiment"].get("kind", "attack") in ("attack", "analysis"), "Unknown experiment kind")
        relative(claim["experiment"]["entrypoint"])
        require("candidate/"+claim["experiment"]["entrypoint"] in files,
                "Missing experiment entrypoint")
        integer(claim["experiment"]["trials"], 1, 8)
    return claim


def build_evidence(root, track, candidate=None, allow_draft=False):
    root = Path(root).absolute()
    require(track in TRACKS, "Unknown track")
    files = snapshot(candidate or root / "candidates" / track)
    protected = [PROFILE, COST, POLICY, "requirements.lock", "benchmark.json", "reorg/plan.json", "schemas/claim-v2.schema.json"]
    protected += sorted(p.relative_to(root).as_posix() for p in
                        (root / "evaluator").glob("*.py"))
    protected += sorted(p.relative_to(root).as_posix() for p in
                        (root / "scripts").glob("*.py"))
    protected += sorted(p.relative_to(root).as_posix() for p in
                        (root / ".github/workflows").glob("*.yml"))
    protected += [".yukon/setup.sh"]
    for path in protected:
        data = read_file(root / path)
        files[path] = {"sha256": sha(data), "text": data.decode("utf-8")}
    profiles, cost, policy = (parse(files[x]["text"]) for x in (PROFILE, COST, POLICY))
    validate_policy(policy)
    manifest = parse(files["benchmark.json"]["text"])
    require(manifest["schemaVersion"] == 2 and manifest["name"] == "curvesmash" and
            len(manifest["tracks"]) == 2 and {t["name"] for t in manifest["tracks"]} == set(TRACKS),
            "Invalid protected track registry")
    for track_config in manifest["tracks"]:
        name = track_config["name"]
        require(track_config["editablePaths"] == ["candidates/"+name] and
                track_config["scorePath"] == ".yukon/scores/"+name+".json" and
                track_config["direction"] == "-" and track_config["promotionMode"] == "manual",
                "Invalid participant boundary or promotion contract")
    # Pin every dependency version, not just the direct imports. Installation uses artifact hashes.
    import re
    for name, version in re.findall(r"^([A-Za-z0-9_-]+)==([^\s]+)",
                                   files["requirements.lock"]["text"], re.MULTILINE):
        require(importlib.metadata.version(name) == version, "Organizer dependency version mismatch")
    require(profiles["id"] == "production-v2" and cost["id"] == "classical-group-work-v2"
            and cost["word_bits"] == 256 and cost["time_unit"] == "target-group-operations"
            and cost["success_probability_minimum"] == 0.39
            and {x["id"] for x in profiles["targets"]} == set(TRACKS),
            "Wrong protected definitions")
    claim = validate_claim(files, track, profiles, cost, allow_draft)
    runtime = {x: importlib.metadata.version(x) for x in ("cryptography", "py-ecc")}
    envelope = {"schema_version": 1, "track": track, "files": dict(sorted(files.items())),
                "claim": claim, "runtime": runtime,
                "experiment_required": "experiment" in claim}
    return {"binding": digest(envelope), "evidence": envelope}


def check_evidence(record):
    exact(record, ("binding", "evidence"))
    require(type(record["binding"]) is str and HEX.fullmatch(record["binding"]) and
            digest(record["evidence"]) == record["binding"],
            "Corrupt evidence envelope")
    evidence = record["evidence"]
    exact(evidence, ("schema_version", "track", "files", "claim", "runtime", "experiment_required"))
    require(evidence["schema_version"] == 1 and evidence["track"] in TRACKS,
            "Invalid evidence identity")
    for path, file in evidence["files"].items():
        relative(path)
        exact(file, ("sha256", "text"))
        require(type(file["text"]) is str and sha(file["text"].encode("utf-8")) == file["sha256"],
                "Evidence file checksum mismatch")
    require(parse(evidence["files"]["candidate/claim.json"]["text"]) == evidence["claim"],
            "Duplicated claim differs from frozen source")
    require(type(evidence["experiment_required"]) is bool and
            evidence["experiment_required"] == ("experiment" in evidence["claim"]),
            "Experiment declaration differs from frozen claim")
    return evidence


def validate_policy(policy):
    exact(policy, ("schema_version", "id", "reviewers", "definition_approvers",
        "maximum_review_age_days", "maximum_definition_age_days", "minimum_distinct_initial_reviewers",
        "experiment_image", "experiment_max_trials", "experiment_timeout_seconds",
        "experiment_memory_bytes", "experiment_output_bytes", "provider"))
    require(policy["schema_version"] == 2 and policy["id"] == "exploratory-review-v1",
            "Unknown review policy")
    require(type(policy["minimum_distinct_initial_reviewers"]) is int and
            policy["minimum_distinct_initial_reviewers"] == 4, "Four independent initial identities required")
    for key in ("reviewers", "definition_approvers"):
        require(type(policy[key]) is dict and len(policy[key]) <= 64, "Invalid organizer key registry")
        for name, authority in policy[key].items():
            text(name, 128)
            exact(authority, ("public_key", "roles"))
            require(type(authority["public_key"]) is str and HEX.fullmatch(authority["public_key"]),
                    "Invalid public key")
            roles = authority["roles"]
            require(type(roles) is list and roles and len(set(roles)) == len(roles) and
                    set(roles) <= ({"definitions"} if key == "definition_approvers" else
                    {"evaluability", "cryptanalysis", "cost", "experiments", "defender", "adjudicator", "execution"}),
                    "Invalid reviewer roles")
    require(not ({x["public_key"] for x in policy["reviewers"].values()} &
                 {x["public_key"] for x in policy["definition_approvers"].values()}),
            "Scientific definition approval must use a separate authority key")
    integer(policy["maximum_review_age_days"], 1, 30)
    integer(policy["maximum_definition_age_days"], 1, 365)
    integer(policy["experiment_max_trials"], 1, 8)
    integer(policy["experiment_timeout_seconds"], 1, 30)
    integer(policy["experiment_memory_bytes"], 32*1024*1024, 512*1024*1024)
    integer(policy["experiment_output_bytes"], 1024, 65536)
    if policy["experiment_image"] is not None:
        import re
        require(type(policy["experiment_image"]) is str and
                re.fullmatch(r"[A-Za-z0-9./:_-]+@sha256:[0-9a-f]{64}", policy["experiment_image"]),
                "Immutable image digest required")
    provider = policy["provider"]
    exact(provider, ("endpoint", "models", "timeout_seconds", "max_tokens"))
    require(provider["endpoint"] == "https://openrouter.ai/api/v1/chat/completions",
            "Invalid organizer provider endpoint")
    require(type(provider["models"]) is dict and set(provider["models"]) <=
            {"evaluability", "cryptanalysis", "cost", "experiments", "defender", "adjudicator"}, "Invalid provider roles")
    for model in provider["models"].values():
        text(model, 256)
    integer(provider["timeout_seconds"], 1, 600)
    integer(provider["max_tokens"], 1024, 16000)
