"""Authenticated review and deterministic exploratory qualification. No model voting."""
from datetime import datetime, timezone, timedelta
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .common import (canonical, digest, exact, text, number, integer,
                     decimal_integer, require, parse, HEX)
from .intake import POLICY, log2_upper, check_evidence, validate_policy

DOMAIN = b"curvesmash-organizer-record-v1\x00"
OBLIGATIONS = {
    "evaluability": ("target", "algorithm", "evidence", "disclosures"),
    "cryptanalysis": ("correctness", "success", "distribution", "heuristics"),
    "cost": ("total_work", "preprocessing_advice", "memory", "arithmetic", "parallelism"),
    "experiments": ("relevance", "reproducibility", "statistics", "extrapolation"),
}


def sign(body, private_bytes):
    key = Ed25519PrivateKey.from_private_bytes(private_bytes)
    return {"body": body, "signature": key.sign(DOMAIN+canonical(body)).hex()}


def verify(record, policy, permission, binding, now=None):
    exact(record, ("body", "signature"))
    body = record["body"]
    require(type(body) is dict and body.get("binding") == binding, "Wrong review binding")
    reviewer = text(body.get("reviewer"), 128)
    registry = policy["definition_approvers"] if permission == "definitions" else policy["reviewers"]
    require(reviewer in registry, "Unauthorized reviewer")
    authority = registry[reviewer]
    exact(authority, ("public_key", "roles"))
    require(permission in authority["roles"], "Reviewer not authorized for this role")
    require(type(authority["public_key"]) is str and HEX.fullmatch(authority["public_key"]),
            "Invalid organizer public key")
    require(type(record["signature"]) is str and len(record["signature"]) == 128,
            "Invalid signature encoding")
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(authority["public_key"])).verify(
            bytes.fromhex(record["signature"]), DOMAIN+canonical(body))
    except (ValueError, InvalidSignature) as exc:
        raise ValueError("Invalid review signature") from exc
    issued = datetime.fromisoformat(text(body.get("issued_at"), 64).replace("Z", "+00:00"))
    require(issued.utcoffset() == timedelta(0), "Review timestamp must be UTC")
    now = now or datetime.now(timezone.utc)
    days = policy["maximum_definition_age_days" if permission == "definitions"
                  else "maximum_review_age_days"]
    integer(days, 1, 365)
    require(now-timedelta(days=days) <= issued <= now+timedelta(minutes=5),
            "Expired or future-dated review")
    return body


def cite(items, evidence):
    require(type(items) is list and 0 < len(items) <= 64, "Missing bounded citations")
    for item in items:
        exact(item, ("path", "sha256", "lines"))
        require(item["path"] in evidence["files"], "Citation outside bound evidence")
        file = evidence["files"][item["path"]]
        require(item["sha256"] == file["sha256"], "Citation hash mismatch")
        lines = item["lines"]
        require(type(lines) is list and len(lines) == 2, "Invalid citation range")
        integer(lines[0], 1, len(file["text"].splitlines()))
        integer(lines[1], lines[0], len(file["text"].splitlines()))


def assessment(value, evidence):
    exact(value, ("id", "status", "reason", "citations"))
    text(value["id"], 128)
    text(value["reason"])
    cite(value["citations"], evidence)


def definitions_binding(evidence):
    return digest({"files": {k: v for k, v in evidence["files"].items()
                              if not k.startswith("candidate/")}, "runtime": evidence["runtime"]})


def initial(record, evidence, binding, policy):
    role = record.get("body", {}).get("role")
    require(role in OBLIGATIONS, "Unknown initial review role")
    body = verify(record, policy, role, binding)
    keys = ("kind", "reviewer", "issued_at", "binding", "role", "provenance",
            "obligations", "heuristics", "findings", "reconstruction", "experiment_report_sha256")
    exact(body, keys)
    require(body["kind"] == "review", "Wrong record kind")
    if evidence["experiment_required"]:
        require(type(body["experiment_report_sha256"]) is str and
                HEX.fullmatch(body["experiment_report_sha256"]), "Review must bind execution evidence")
    else:
        require(body["experiment_report_sha256"] is None, "Unexpected experiment binding")
    provenance = body["provenance"]
    exact(provenance, ("kind", "model", "request_id", "prompt_sha256"))
    require(provenance["kind"] in ("human", "ai"), "Invalid reviewer provenance")
    for field in ("model", "request_id", "prompt_sha256"):
        text(provenance[field], 256)
    obligations = body["obligations"]
    require(type(obligations) is list and len(obligations) == len(OBLIGATIONS[role]),
            "Missing review obligations")
    require({x.get("id") for x in obligations} == set(OBLIGATIONS[role]),
            "Review obligation coverage mismatch")
    for obligation in obligations:
        assessment(obligation, evidence)
        require(obligation["status"] in ("supported", "not_applicable", "unresolved"), "Invalid obligation status")
    heuristics = body["heuristics"]
    require(type(heuristics) is list and len(heuristics) <= 64, "Invalid heuristic coverage")
    expected_ids = {h["id"] for h in evidence["claim"]["heuristics"]}
    actual_ids = {h.get("id") for h in heuristics}
    require(len(actual_ids) == len(heuristics), "Duplicate heuristic assessment")
    if role in ("cryptanalysis", "experiments"):
        require(expected_ids <= actual_ids, "Every heuristic needs both substantive reviews")
    for heuristic in heuristics:
        assessment(heuristic, evidence)
        require(heuristic["status"] in ("established", "plausible", "unsupported", "refuted"),
                "Invalid heuristic status")
    findings = body["findings"]
    require(type(findings) is list and len(findings) <= 64, "Invalid findings")
    ids = set()
    for finding in findings:
        exact(finding, ("id", "severity", "reason", "citations", "obligations", "heuristic_ids"))
        text(finding["id"], 128)
        require(finding["id"] not in ids, "Duplicate finding ID")
        ids.add(finding["id"])
        require(finding["severity"] in ("fatal", "unresolved", "note"), "Invalid finding severity")
        text(finding["reason"])
        cite(finding["citations"], evidence)
        require(type(finding["obligations"]) is list and finding["obligations"]
                and set(finding["obligations"]) <= set(OBLIGATIONS[role]),
                "Finding must identify affected obligations")
        require(type(finding["heuristic_ids"]) is list and
                set(finding["heuristic_ids"]) <= expected_ids | actual_ids, "Unknown challenged heuristic")
    for heuristic in heuristics:
        if heuristic["status"] == "refuted":
            require(any(f["severity"] == "fatal" and heuristic["id"] in f["heuristic_ids"]
                        for f in findings), "Refuted heuristic needs a challengeable fatal finding")
    reconstruction = body["reconstruction"]
    if role == "cost":
        exact(reconstruction, ("time_log2", "memory_log2_bytes", "preprocessing_log2",
                               "nonuniform_advice_log2_bytes", "success_probability"))
        for field in ("time_log2", "memory_log2_bytes", "preprocessing_log2",
                      "nonuniform_advice_log2_bytes"):
            number(reconstruction[field], 0, 2048)
        number(reconstruction["success_probability"], 0, 1)
        statuses = {item["id"]: item["status"] for item in body["obligations"]}
        for obligation in cost_discrepancies(reconstruction, evidence["claim"]["claim"]):
            require(statuses[obligation] != "supported" or any(
                f["severity"] == "fatal" and obligation in f["obligations"] for f in findings),
                "Supported cost contradicts submitted bound without a linked fatal finding")
    else:
        require(reconstruction is None, "Only cost review reconstructs resource bounds")
    return body


def cost_discrepancies(reconstruction, bounds):
    mapping = {"time_log2": "total_work", "memory_log2_bytes": "memory",
               "preprocessing_log2": "preprocessing_advice",
               "nonuniform_advice_log2_bytes": "preprocessing_advice"}
    result = {obligation for field, obligation in mapping.items()
              if reconstruction[field] > bounds[field] + 1e-6}
    if reconstruction["success_probability"] + 1e-6 < bounds["success_probability"]:
        result.add("total_work")
    return result


def template(record, role, reviewer, experiment=None):
    """Unresolved template; never manufacture approval or sign it automatically."""
    evidence = record["evidence"]
    path = "candidate/"+evidence["claim"]["proof"]
    citations = [{"path": path, "sha256": evidence["files"][path]["sha256"], "lines": [1, 1]}]
    def item(id):
        return {"id": id, "status": "unresolved", "reason": "Review required.", "citations": citations}
    bounds = evidence["claim"]["claim"]
    reconstruction = {k: bounds[k] for k in ("time_log2", "memory_log2_bytes",
        "preprocessing_log2", "nonuniform_advice_log2_bytes", "success_probability")} if role == "cost" else None
    return {"kind": "review", "reviewer": reviewer,
        "issued_at": datetime.now(timezone.utc).isoformat(), "binding": record["binding"],
        "role": role, "provenance": {"kind": "human", "model": "human", "request_id": "manual",
                                      "prompt_sha256": digest(OBLIGATIONS)},
        "obligations": [item(x) for x in OBLIGATIONS[role]],
        "heuristics": [dict(item(h["id"]), status="unsupported") for h in
                       evidence["claim"]["heuristics"]] if role in ("cryptanalysis", "experiments") else [],
        "findings": [], "reconstruction": reconstruction,
        "experiment_report_sha256": digest(experiment) if experiment else None}


def aggregate(record, reviews, challenges=(), definition_approval=None, experiment=None):
    evidence, binding = check_evidence(record), record["binding"]
    policy = parse(evidence["files"][POLICY]["text"])
    validate_policy(policy)
    initial_records, bodies = {}, {}
    for review in reviews:
        body = initial(review, evidence, binding, policy)
        require(body["experiment_report_sha256"] == (digest(experiment) if experiment else None),
                "Review is bound to different execution evidence")
        require(body["role"] not in bodies, "Duplicate initial review role")
        bodies[body["role"]] = body
        initial_records[body["role"]] = review
    # Count distinct keys, not reviewer aliases. Model diversity is not implied.
    keys = {policy["reviewers"][b["reviewer"]]["public_key"] for b in bodies.values()}
    blockers = []
    missing = set(OBLIGATIONS)-set(bodies)
    if missing:
        blockers.append("Missing review roles: "+", ".join(sorted(missing)))
    if len(keys) < policy["minimum_distinct_initial_reviewers"]:
        blockers.append("Insufficient independent initial reviewer identities")
    obligations = {(role, x["id"]): x["status"] for role, b in bodies.items()
                   for x in b["obligations"]}
    findings = {(digest(initial_records[role]), f["id"]): (role, f)
                for role, b in bodies.items() for f in b["findings"] if f["severity"] == "fatal"}
    resolved, confirmed, resolutions = set(), [], {}
    for challenge in challenges:
        exact(challenge, ("defense", "adjudication"))
        defense = verify(challenge["defense"], policy, "defender", binding)
        adjudication = verify(challenge["adjudication"], policy, "adjudicator", binding)
        exact(defense, ("kind", "reviewer", "issued_at", "binding", "review_sha256",
                        "finding_id", "reason", "citations"))
        exact(adjudication, ("kind", "reviewer", "issued_at", "binding", "review_sha256",
                             "finding_id", "defense_sha256", "decision", "reason", "citations",
                             "discharged_obligations"))
        require(defense["kind"] == "defense" and adjudication["kind"] == "adjudication",
                "Wrong challenge record kinds")
        key = (defense["review_sha256"], defense["finding_id"])
        require(key in findings and key not in resolved, "Unknown or duplicate finding resolution")
        require((adjudication["review_sha256"], adjudication["finding_id"]) == key and
                adjudication["defense_sha256"] == digest(challenge["defense"]), "Wrong defense binding")
        role, finding = findings[key]
        identities = [bodies[role]["reviewer"], defense["reviewer"], adjudication["reviewer"]]
        require(len({policy["reviewers"][x]["public_key"] for x in identities}) == 3,
                "Finding, defense and adjudication need distinct identities")
        for body in (defense, adjudication):
            text(body["reason"])
            cite(body["citations"], evidence)
        decision = adjudication["decision"]
        require(decision in ("confirmed", "dismissed", "unresolved"), "Invalid adjudication")
        discharged = adjudication["discharged_obligations"]
        require(type(discharged) is list and len(set(discharged)) == len(discharged)
                and set(discharged) <= set(finding["obligations"]), "Unlinked obligation discharge")
        require(decision == "dismissed" or not discharged, "Cannot discharge an unresolved finding")
        resolved.add(key)
        resolutions[key]=decision
        if decision == "confirmed" and finding["severity"] == "fatal":
            confirmed.append(key)
        elif decision != "dismissed":
            blockers.append("Unresolved finding: "+finding["id"])
        else:
            for id in discharged:
                obligations[(role, id)] = "supported"
    for key in set(findings)-resolved:
        blockers.append("Fatal finding awaits defense/adjudication: "+key[1])
    evaluability_gaps = [id for (role, id), status in obligations.items()
                        if role == "evaluability" and status not in ("supported", "not_applicable")]
    unsupported = [role+"/"+h["id"] for role, body in bodies.items()
                   for h in body["heuristics"] if h["status"] == "unsupported"]
    # Keep uncertainties visible without requiring the rigorous lane's discharge gate.
    uncertainties = [role+"/"+id for (role, id), status in obligations.items()
                     if status not in ("supported", "not_applicable")]
    heuristic_assessments={}
    for role,body in bodies.items():
        for h in body['heuristics']:
            linked=[key for key,(finding_role,f) in findings.items()
                    if finding_role==role and h['id'] in f['heuristic_ids']]
            status=h['status']
            if status=='refuted':
                decisions=[resolutions.get(key,'unresolved') for key in linked]
                status='refuted' if 'confirmed' in decisions else 'pending_reassessment' if decisions and all(d=='dismissed' for d in decisions) else 'unresolved_refutation'
            heuristic_assessments[role+'/'+h['id']]={'review_status':h['status'],'effective_status':status,
                'linked_fatal_findings':[list(key) for key in linked]}
            if status!='established':uncertainties.append(role+'/heuristic/'+h['id']+': '+status)
    uncertainties += [role+"/"+f["id"] for role, body in bodies.items()
                      for f in body["findings"] if f["severity"] == "unresolved"]
    all_ids = {h['id'] for body in bodies.values() for h in body['heuristics']}
    for role in ('cryptanalysis','experiments'):
        assessed = {h['id'] for h in bodies.get(role,{}).get('heuristics',[])}
        uncertainties += [role+'/unreviewed-heuristic/'+id for id in all_ids-assessed]
    # A signed organizer receipt is optional provenance, never scientific evidence.
    if definition_approval is not None:
        approval = verify(definition_approval, policy, "definitions", definitions_binding(evidence))
        exact(approval, ("kind", "reviewer", "issued_at", "binding", "decision", "reason"))
        require(approval["kind"] == "definitions" and approval["decision"] == "approved",
                "Invalid optional organizer receipt")
        text(approval["reason"])
    if evidence["experiment_required"]:
        if experiment is None:
            blockers.append("Declared experiments missing")
        else:
            from .experiments import validate_report
            validate_report(experiment, record, policy)
    else:
        require(experiment is None, "Unexpected experiment record")
    if missing or len(keys) < policy["minimum_distinct_initial_reviewers"] or set(findings)-resolved or (evidence["experiment_required"] and experiment is None):
        state = "infra_failed"
    elif confirmed:
        state = "refuted"
    elif evaluability_gaps or unsupported:
        state = "not_evaluable"
        blockers += ["Evaluability: "+x for x in evaluability_gaps] + ["Unsupported heuristic: "+x for x in unsupported]
    else:
        state = "plausible_not_refuted"
        uncertainties += blockers
        blockers = []
    if not reviews and not challenges:
        state = "pending_review"
    return {"schema_version": 1, "binding": binding, "track": evidence["track"],
        "outcome": state, "heuristic_assessments": heuristic_assessments, "uncertainties": sorted(set(uncertainties)), "policy": "exploratory-review-v1", "blockers": sorted(set(blockers)), "confirmed_findings": [list(x) for x in confirmed],
        "reviews": list(reviews), "challenges": list(challenges), "definition_approval": definition_approval,
        "experiment": experiment, "claim_kind": evidence["claim"]["baseline_kind"],
        "meaning": "Reviewed complexity claim; qualification is not a proof, measured attack, novelty claim or promotion."}


def score(record, dossier):
    """Reconstruct qualification; never trust a dossier's outcome flag."""
    require(dossier["binding"] == record["binding"], "Stale dossier")
    rebuilt = aggregate(record, dossier["reviews"], dossier["challenges"],
                        dossier["definition_approval"], dossier["experiment"])
    require(rebuilt == dossier and rebuilt["outcome"] == "plausible_not_refuted", "Dossier does not qualify")
    claim = record["evidence"]["claim"]["claim"]
    value = claim["time_log2"]
    return {"score": value, "timeLog2": value,
            "binding": record["binding"], "dossier_sha256": digest(dossier),
            "track": rebuilt["track"], "claim_kind": rebuilt["claim_kind"],
            "policy": rebuilt["policy"], "timeUnit": claim["time_unit"],
            "memoryLog2Bytes": claim["memory_log2_bytes"], "promotionMode": "manual"}
