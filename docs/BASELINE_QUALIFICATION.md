# Baseline qualification

Both baselines passed ordinary live qualification on 12 October 2026 using protected source [`709b01339a7764a884a3a0554b0ae9152716f1c4`](https://github.com/zac-williamson/curvesmash/tree/709b01339a7764a884a3a0554b0ae9152716f1c4). Each run completed intake, four separate initial AI reviews and credential-free scoring. Both outcomes are `plausible_not_refuted`, with no confirmed fatal findings, blockers or infrastructure errors.

| Track | Qualified score | Live qualification |
| --- | ---: | --- |
| secp256k1 discrete logarithm | 129.000802 | [38266376662](https://github.com/zac-williamson/curvesmash/actions/runs/38266376662) |
| BLS12-381 fixed-G2 pairing inversion | 128.494762 | [38266381573](https://github.com/zac-williamson/curvesmash/actions/runs/38266381573) |

Scores are log2(total computation in the track's fixed target-group-operation equivalents), lower is better. The controls use standard baby-step/giant-step with success probability 1. They are conservative accounting controls, not best-known attack estimates, practical breaks or new cryptanalysis. The four initial calls use the same configured model, `openai/gpt-5.6-sol`; no model diversity or statistical independence is claimed.

The BLS cost reviewer recorded one nonfatal note: challenge-independent setup also belongs under preprocessing. Setup is already included in total work, and moving it does not change the rounded preprocessing bound or score. The note is preserved in the dossier. Neither dossier reports additional uncertainties; that does not turn exploratory acceptance into a mathematical proof.

The downloaded GitHub artifact ZIPs were checked against their published SHA-256 digests. Signed reviews, exact evidence bindings and score reconstruction were verified independently of the workflow outcome flags. Dossier SHA-256 values:

- secp256k1: `528f4c933de88bbc54715bfe266d5adf21a82590620e087727a26139c17ad6ff`
- BLS12-381: `d7eb07b11f032b30d9f6e12d72bbb0b44b861badc8071804d7396b918590dc21`

The [v0.2.0 public release](https://github.com/zac-williamson/curvesmash/releases/tag/v0.2.0) contains source and evidence archives, their checksums, original artifact ZIPs, extracted records and run/artifact metadata. It preserves earlier attempts, including failures and objections, rather than retaining only favorable reviews. Actions artifacts expire after 30 days; the release preserves the historical evidence, while fresh scoring still follows the published signature and expiry rules.

Live reassessment checks also passed for [secp256k1](https://github.com/zac-williamson/curvesmash/actions/runs/38259364778) and [BLS12-381](https://github.com/zac-williamson/curvesmash/actions/runs/38259370351), preserving both scores exactly. Those temporary pins were cleared before the final ordinary runs; the active reassessment plan is empty.

The source passed all 80 tests in [CI](https://github.com/zac-williamson/curvesmash/actions/runs/38266286174), including actual container execution and acceptance, signature, isolation and reassessment failure paths. This checks implementation behavior, not a measured scientific error rate for the judge.

Yukon benchmark-owner/import access is still pending. The repository and evidence are public, but the challenge is not yet registered and submissions are not open. There is no live domain deployment.

The [version 1 record](archive/BASELINE_QUALIFICATION_V1.md) is retained as history. Its word-operation scores and stricter policy are retired and cannot be presented as current results. No new cryptanalytic attack is claimed by the change in policy or units.
