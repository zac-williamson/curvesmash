# Evaluation contract

Exactly two production targets, one rigorous acceptance policy, and one work metric. No exploratory leaderboard. This implementation follows [HashSmash's review obligations and challenge process](https://github.com/Layr-Labs/hash-smash/blob/main/docs/JUDGE_LANES.md), specialized to ECDLP and fixed-generator pairing inversion. No upstream implementation is copied.

## What the evaluator establishes

Intake checks the submission's structure, definition bindings, exact work sum, preprocessing subset, peak memory, success threshold and upward-rounded logarithms. It freezes every file as inert UTF-8 text. These checks do **not** establish the algorithm, primitive-operation ledger, probability argument or scientific novelty.

Four independent initial review calls cover evaluability, cryptanalysis, cost and experiments. Every role must discharge every assigned obligation with substantive reasoning and file/hash/line citations. Cryptanalysis and experiments must each assess every declared heuristic as established in its claimed regime. Plausible, unsupported and unresolved claims receive no score. Implicit assumptions must be recorded as findings.

A fatal objection needs a cited concrete flaw. It must receive a defense and an adjudication from separate identities before it can refute a submission. Missing support is unresolved, not a counterexample. Dismissal only discharges explicitly linked obligations; defeating an objection does not establish a heuristic. A new substantive assessment is needed in that case.

The cost reviewer independently reconstructs exact total work, preprocessing, memory, advice and success. A reconstruction exceeding any submitted bound, or reducing its success guarantee, blocks scoring even if the reviewer labels the claim supported. Qualification uses the submitted bound, not a favorable cost estimate invented by the evaluator.

Analytic constructions can qualify without empirical experiments. Declared experiments must finish before review; all four reviews bind the exact authenticated execution report. Finite counts and elapsed time never become a full-size complexity score.

## Submission format

Each candidate has `claim.json`, a self-contained proof and a resource ledger. The existing two packages are concrete examples. The claim has the fixed definition IDs and SHA-256 hashes, `submission_state: ready`, `review_status: pending`, and `baseline_kind: research-claim` or `generic-accounting-control`. Candidates cannot assert organizer acceptance.

The ledger declares:

- `components`: disjoint, exhaustive work components as canonical nonnegative decimal integer strings. Their sum equals `work_budget_word_operations`.
- `preprocessing_components`: a unique subset of component names, charged within total work.
- `peak_memory_bytes`: positive decimal integer string; `advice_bytes`: nonnegative integer included in that peak.
- `success_probability`: identical to the claim's supported lower bound.
- The justified arithmetic/algorithm ledger needed for substantive cost review. Formula strings are inert evidence, never evaluated as code.

Logarithms must equal the evaluator's upward rounding to six decimal places. The exact integers govern accounting. The submission limit is 4 MiB, 128 UTF-8 files, 128 directories, depth 8. Canonical relative paths contain letters, digits, `_`, `-`, and `.` only. Links, hard links, special files, duplicate JSON keys, nonfinite numbers and NULs are rejected. Initial executable experiment support is Python; analytic claims can describe other algorithms without executing them.

## Trust and artifacts

Use a trusted organizer checkout and the hash-locked environment. Only candidate directories are participant-editable. Never load organizer code, policies or keys from a submission checkout. The deployment must enforce this boundary; local path checks cannot protect an organizer who chooses an untrusted evaluator.

The evidence binding covers all candidate bytes, both complete definitions, track manifest, review policy, every evaluator module, dependency lock and direct runtime versions. Scoring rebuilds this envelope from current trusted files. Changes invalidate every bound review and approval. Reviewer citations bind immutable file bytes and valid line ranges. Output artifacts are published atomically and never replace existing files.

`evaluation/policy-v1.json` is the protected authority registry. Provision raw Ed25519 public keys and exact allowed roles; keep private service keys outside repositories, submission mounts and artifacts. Four distinct initial signing keys are required; aliases of one key do not count. Signatures authenticate the organizer service's provenance assertion, not the truth of its reasoning or independence of its underlying model. Model diversity is configurable and must be reported honestly.

Reviews expire after 30 days; definition/evaluator approvals after 365 days. The scientific definition approver signs `definitions_binding(evidence)` with `kind: definitions`, `decision: approved`, UTC issue time and a substantive reason. Approval is a separate record so it does not silently alter the bound specifications. Revoking a key changes the policy and invalidates existing qualification. Reassessment must retain prior dossiers in the organizer archive.

The scorer verifies authorization, signatures, freshness, stage coverage, citations, challenge bindings, reconstruction and scientific approval again. An outcome flag in a JSON file is never authority. It emits `timeLog2` only for a qualified dossier, preserves memory and claim kind, and refuses existing score files. Yukon promotion remains a separate human decision.

Outcomes: `pending_review`, `not_qualified`, `refuted`, `qualified`. Invalid schemas, signatures, provider responses or stale bindings are infrastructure failures, never scientific refutations. No majority vote or model-confidence threshold is used. Qualification is a reviewed complexity claim, not mathematical proof, practical attack execution, novelty or promotion.

## Commands

Create a fresh evidence envelope and pending dossier for either track:

```sh
.venv/bin/python -m evaluator.cli prepare --track secp256k1-ecdlp --output .yukon/reports/secp-evidence.json
.venv/bin/python -m evaluator.cli qualify --evidence .yukon/reports/secp-evidence.json --output .yukon/reports/secp-dossier.json
```

`qualify` returns 2 when scientific gates remain outstanding, 0 when qualified, and 1 for invalid infrastructure. It never writes a score. The same commands accept `bls12-381-invert-g1`. Intake also accepts `--candidate` for a separately extracted submission; supply the same directory to subsequent commands. Do not unpack archives into the organizer checkout.

For human review, `template --evidence ... --role cost --reviewer NAME --output ...` produces an **unresolved** body. Complete the argument and citations, then `sign --body ... --key /protected/service.key --output ...`. A template is not approval. `sign` authenticates bytes; qualification still validates their full schema and authority.

For AI review, configure exact provider model IDs per role in the protected policy. Run `review --evidence ... --role ROLE --reviewer NAME --key /protected/service.key --output ...` in the credentialed review job with `OPENROUTER_API_KEY`. Each call sees the same evidence and no peer verdicts. Responses must match the structured schema and configured model; truncation, tool requests, redirects and provider/schema failures block review. Credentials never enter prompts or output artifacts. Do not run this job on participant-controlled infrastructure.

Collect all four signed records with `qualify --evidence ... --reviews ROLE1.json ROLE2.json ROLE3.json ROLE4.json --definition-approval APPROVAL.json --output DOSSIER.json`. Optional `--challenges` accepts records containing a signed defense and signed adjudication, each linked to the original review hash and finding ID; adjudication also binds the signed defense hash. Challenge bodies are defined by `review.aggregate`; their original records remain in the dossier. No new unchallenged finding can be introduced by adjudication.

In a separate credential-free scoring job, run `score --evidence ... --dossier ...`. It recomputes qualification and writes the selected track's protected `.yukon/scores/<track>.json`. No API credentials or private signing keys are needed. Do not combine candidate execution, provider review and final scoring into a credentialed job.

## Optional experiments

An optional claim field `experiment: {entrypoint: attack.py, trials: 1}` requests a bounded number of fresh uniform full-parameter challenges. The attack reads one JSON challenge from standard input and prints one JSON output. It receives no sampling secret. No runtime, image, command, environment or privilege options come from candidates.

An organizer-provisioned image must be pinned by immutable digest and already available. `experiment --evidence ... --reviewer EXECUTOR --key /protected/execution.key --output ...` runs each trial in a fresh container: no network, read-only root and submission, unprivileged user, dropped capabilities, no privilege escalation, bounded memory/CPU/PIDs/files/output/wall time and bounded scratch. Host environment secrets are not forwarded. Timeouts and malformed outputs fail closed; containers are removed. Host verifiers check canonical values, curve/subgroup membership and exact output equations.

Pass the signed report using `--experiment` to every template/review/qualify call. The report includes public challenge/output pairs and verification results; no secret scalars. Candidate operation counters are ignored. Deploy experiments on disposable dedicated workers with no credentials or sensitive mounts; a container is not a substitute for that host boundary.

## Before opening submissions

The code is implemented and tested, but production keys, models, image and scientific approval are deliberately unprovisioned. CI uses synthetic organizer fixtures; its successful approvals are temporary test data, never baseline qualification or measurements of AI judge quality.

Required work for our launch policy: scientific approval of definitions, verifiers and cost accounting; blinded human-labeled judge calibration with held-out errors reported; qualifying live review of a starting baseline for each track; separated trusted Yukon jobs and manual promotion verified; public evidence archiving and the two-row results page. This policy must be distinguished from Yukon's platform requirements. A fully accounted generic control is eligible for initial qualification, consistent with HashSmash; selecting best-known reference attacks is separate research work. Both current packages remain unqualified generic controls. Beating them alone is not a cryptanalytic advance.
