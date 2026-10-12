# Exploratory review

Both tracks use `exploratory-review-v1`, following HashSmash's public exploratory acceptance policy. A submission can score when it is concrete, has relevant support and has no confirmed fatal flaw after defense/adjudication. Remaining scientific uncertainty is published with the result. This outcome is **plausible_not_refuted**, not proof, peer review or evidence of a practical break.

## Sequence

1. Intake checks the claim, exact target/cost bindings and declared files. Drafts do not reach judging. Candidate files are frozen as inert text; only declared experiments may execute in the bounded container.
2. Four separate initial calls inspect the same evidence: evaluability, cryptanalysis, cost and experiments. They receive no other initial verdict. Every role must return valid, signed records with substantive reasoning and citations to bound file lines. Calls currently use the same configured model; model diversity or statistical independence is not assumed.
3. Each fatal objection receives a defense and adjudication. Only a confirmed objection refutes the submission. Unresolved or dismissed objections remain in the dossier; dismissal does not establish the underlying heuristic. Missing challenge records or invalid provider responses are infrastructure failures, never acceptance.
4. The scorer checks record authority, signatures, freshness, bindings, citations and stage coverage. An evaluability gap or unsupported heuristic prevents scoring. Established or plausible heuristics can support exploratory acceptance. Other unresolved obligations and material concerns remain visible without being turned into a rigorous-review gate.
5. Accepted ordinary submissions receive their submitted computation bound. Memory is supplementary. A supported resource reconstruction contradicting the claim must raise a linked fatal objection; an unexplained contradictory review is invalid.

No separate "scientific approval" receipt is required to produce an exploratory score. The organizer pins the protected release; participants cannot alter it. Manual promotion through Yukon remains a separate decision after qualification and improvement over the current incumbent.

## Evidence and execution

The evidence binding covers candidate bytes, target/cost definitions, claim schema, review policy, dependencies, evaluator, scripts, workflows, setup and reassessment plan. Changing bound inputs requires a new review or an explicitly pinned reassessment. Generated outcome flags are not authority.

Provider credentials and private signing keys reach only the review job. Intake/experiments and scoring use separate workers. Experiments have no network, secret environment or sensitive mounts; candidate code never executes on the host. The isolated worker proves execution of the submitted program, not the truth of an extrapolated cryptanalytic claim.

Reviews expire after 30 days. Historical reassessment packets preserve earlier judgments without replaying today's schema or expiry rules against them. Current reassessments receive current signatures, expiry and score checks. Preserve every attempt, including failures and objections; do not select only favorable reviews.

## Outcomes

- `plausible_not_refuted`: eligible for an exploratory score; uncertainties are retained.
- `refuted`: a fatal flaw survives adjudication; no score.
- `not_evaluable`: required specification or supporting evidence is absent; no score.
- `infra_failed`: a required record, provider response or binding failed; no score.
- `pending_review`: no completed review; no score.

Blinded human-labeled cases and held-out measurements are needed before claiming measured judge error rates. Our software tests establish aggregation and isolation behavior; our live baseline reviews do not measure judge accuracy. The two generic controls are not best-known attacks, and beating them alone does not establish a cryptanalytic advance.

See [TASK.md](../TASK.md) for participation, [execution](EXECUTION.md) for provisioning, [cost rules](COST_MODEL.md), and [reassessment](RESCORING.md).
