# Yukon challenge application

Repository: [zac-williamson/curvesmash](https://github.com/zac-williamson/curvesmash), public. Owner: zac-williamson. This file is the application text, not evidence that Yukon has registered the challenge.

## Goal metric

Minimize the computation needed to solve secp256k1 discrete logarithms or invert the BLS12-381 pairing. Each problem has a separate leaderboard. Scores are log2 of total computation under a fixed reference-operation cost model; lower is better. Algorithms must succeed on at least 39% of uniformly random challenges. Preprocessing and failed attempts count.

## Objective scoring

Submissions describe the attack, justify its success probability and explain all computation costs in a written argument. AI reviewers assess the algorithm, costs and supporting experiments against published exploratory rules, following HashSmash. Fatal objections receive defense and adjudication. A concrete, supported submission with no confirmed fatal flaw receives its submitted computation bound as the score; remaining uncertainty is published. Review acceptance is not mathematical proof. Improved scores require owner approval before Yukon promotion.

## Integration

Please grant production benchmark-owner/import access, install the production GitHub App and import both tracks from the root manifest with submissions initially closed. We need to verify baseline runs, score-artifact ingestion, protected candidate paths and the manual promotion lifecycle before opening. No website or production import is claimed by this application.
