# Initial baseline qualification

Both starting baselines qualified under the project's AI review policy and emitted verified scores on October 12, 2026. They use deterministic baby-step/giant-step at full production parameters, with success probability 1. Their computation and storage are impractical. These results establish accounting controls for the benchmark, not new attacks or security estimates.

| Target | Score: log2 word operations | log2 peak bytes | Review run | Successful scoring run |
| --- | ---: | ---: | --- | --- |
| secp256k1 discrete logarithm | 155.218461 | 136.000001 | [38250816640](https://github.com/zac-williamson/curvesmash/actions/runs/38250816640) | [38252122034](https://github.com/zac-williamson/curvesmash/actions/runs/38252122034) |
| BLS12-381 pairing inversion into G1 | 153.944862 | 137.643857 | [38250820486](https://github.com/zac-williamson/curvesmash/actions/runs/38250820486) | [38252151330](https://github.com/zac-williamson/curvesmash/actions/runs/38252151330) |

## Evidence and authorization

The candidate and evaluator release was [d65fcfb71f18d989baa5084561557fa3ef147d43](https://github.com/zac-williamson/curvesmash/tree/d65fcfb71f18d989baa5084561557fa3ef147d43). Four initial roles used separate calls to `openai/gpt-5.6-sol` with high reasoning. All assigned obligations were discharged; there were no findings or infrastructure errors in these final review runs. Earlier attempts remain in the organizer archive, including the pairing-accounting objection that required a substantive candidate correction and citation-transport failures that emitted no scores.

After receiving a plain-language explanation, Zac Williamson explicitly authorized using the rules for initial baseline qualification. The signed receipt records this organizer decision; it does not assert independent human cryptanalytic validation, mathematical proof, public-launch approval or Yukon registration. Its protected-definition binding is `8f354784c01a337d2458b48d278b5b5bd8f31110dd222bb64ea4c863a13ca705`. The protected specifications retain their pending independent-scientific-review status. Qualification is established by the authenticated dossiers rather than by editing the frozen candidate packages' original status descriptions.

The scoring jobs repeated intake and reused the completed reviews without further provider calls. Both jobs verified review signatures, citations, resource reconstructions, expiry and organizer approval before writing the named `benchmark-score-<track>` artifact at the manifest's exact score path. The exported score objects were independently reconstructed from their dossiers and matched exactly. Every exported ZIP matched GitHub's artifact SHA-256 digest. The release's CI passed 71 tests, including live container isolation.

Final dossier hashes:

- secp256k1: `92774e09e826ae4c7e4ad384bc1434481111c1f423fbe6ebf4e4b495ab16335e`
- BLS12-381: `02a0d1c05546f25d09fc4f3f73dba7f9f20102618f8ba21ea4136dafb4095419`

Organizer exports are retained outside Git under `.yukon/reports/github/<run-id>/`, including artifact metadata, verified archives, intake and qualification dossiers. Original review artifacts are retained under their review run IDs. The approval receipt is at `.yukon/reports/d65fcfb/definitions-approval.json`. GitHub artifacts expire after 30 days; a durable public archive is still required before opening submissions.

## Remaining boundary

The repository is private. Yukon has not imported the benchmark or verified its own submission and promotion lifecycle. Independent human cryptanalytic review, judge calibration and the website remain outstanding. Organizer approval and AI qualification do not replace those steps.
