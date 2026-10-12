# Curvesmash launch plan

## Scope to keep fixed

Launch six classical, single-target, unrestricted production tracks: secp256k1 ECDLP, P-256 ECDLP, and inversion into either source group for Ethereum BN254 and BLS12-381. Begin with one public exploratory submission lane per target and manual promotion. Retain stricter scientific assessment in the dossier; decide whether a separate rigorous lane adds value after calibration. Do not create small-curve or interval leaderboards.

## Deliverables and owners

| Deliverable | Responsible role | Acceptance evidence |
| --- | --- | --- |
| Exact target profiles | ECDLP/pairing scientific leads | Reviewed parameter lock, generators, groups, map, encodings, challenge distribution, independent test vectors |
| Total computation contract | Scientific lead and cost reviewer | Priced operation ledger including arithmetic, bookkeeping, randomness, precomputation, advice, failed trials, verification, and amplification |
| Baseline packages | Cryptanalysis researchers | Complete constructions and bounds at actual parameters, citations, assumptions, reviewer signoff |
| Evaluation pipeline | Benchmark engineer | Deterministic intake, immutable binding, credential-free isolated execution, independent checks, bounded provider review, protected scoring |
| Calibration | Scientific committee | Held-out human-labelled valid, flawed, and uncertain claims; observed error analysis and unresolved obligations |
| Yukon integration | Repository owner and Yukon operator | Closed registration, real baseline jobs, actual track IDs, protected-path rejection, owner review/promotion, sibling preservation |
| Website and release | Organizer and Yukon page owner | Results bound to verified records, evidence links, review status, no synthetic production scores, confirmed domain route |

## Evaluation contract to implement

Each submission provides claim metadata, a self-contained mathematical argument, a priced resource ledger, heuristic disclosures, citations/attribution, and declared evidence files. A claim's scalar is an estimated or derived full-size attack cost, not an arbitrary participant runtime or a toy-instance score. Independent execution establishes finite observations only. Review must assess whether those observations support the claimed full-size algorithm.

Bind candidate bytes, exact source revision, target and cost definitions, evidence, and review configuration with content hashes. Changed inputs require new evidence and qualification. Authenticate organizer-produced execution and review artifacts; candidate-controlled JSON cannot assert acceptance. Keep intake/experiments, credentialed model review, and final score construction in separate jobs. A malformed, unsupported, refuted, or infrastructurally failed package emits no score.

Scientific obligations include subgroup validity, full pairing equality, correctness and success model, all charged work, peak storage, valid independence assumptions, scope of experiments, and the extrapolation to production. Reviewers must distinguish a concrete fatal flaw from an unresolved assumption. Expert acceptance and AI assessment are different recorded states.

## Baselines

ECDLP baselines must account for known automorphisms/endomorphisms and implementation costs. Pairing baselines must instantiate a target-group DLP algorithm against the exact field and subgroup, then construct the recovered point. Generic square-root bounds alone may omit a stronger applicable finite-field attack. Select and price the lowest supported applicable baseline under the same resource contract. No baseline number is assigned in this starter.

## Release gates

- Scientific target and cost definitions approved and versioned.
- Baselines individually qualified; pending targets remain unopened.
- Independent point/pairing verification and isolated execution tested.
- Review calibration completed with public limitations.
- Real Yukon validation and manual-promotion lifecycle verified under the selected production App.
- GitHub owner, domain, budget, reviewer availability, license, and publication policy resolved.

There is no reliable time estimate until the baseline and parameter-definition work is scoped. A narrow closed pilot with one ECDLP target and both inversion directions on one pairing curve can verify the lifecycle before all six tracks open. This does not change the metric or introduce a different target class.
