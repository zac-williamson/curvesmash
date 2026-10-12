# Organizer execution

Two GitHub Actions workflows implement the manifest's runner: `secp256k1-ecdlp.yml` and `bls12-381-invert-g1.yml`. Each calls the shared qualification workflow.

1. Intake checks out the immutable organizer release and submitted commit separately, rejects changes outside the selected candidate directory, freezes all evidence and runs declared experiments on a credential-free worker. For a protected reassessment pin, it fetches and authenticates the exact previous review artifact using the GitHub read token.
2. Review uses a new worker. Only its review step receives the provider credential and service signing keys. Ordinary submissions get four initial calls and any required defense/adjudication. Pinned reassessments get one current-policy call with previous judgments. Raw completed attempts and sanitized failure diagnostics are retained.
3. Score uses another worker with no provider or signing credentials. It reconstructs acceptance and emits numeric `score` and `timeLog2` fields only on acceptance. The `benchmark-score-<track>` artifact contains the exact manifest-relative `.yukon/scores/<track>.json` path. Promotion remains manual.

## Provisioning

- `OPENROUTER_API_KEY`: repository Actions secret for the paid review provider; it is not a Yukon token.
- `CURVESMASH_REVIEW_SIGNING_KEYS`: repository Actions secret holding the role-specific organizer service keys. Public authorities are in `evaluation/policy-v2.json`. Private keys remain outside the repository and experiment mounts.
- `CURVESMASH_TRUSTED_SHA`: repository variable containing the full reviewed organizer commit. Participants cannot replace this release or its workflows.

The policy pins the exact provider model and immutable experiment image. Initial roles use separate requests and signing keys but the same model. There is no separate scientific-approval secret or receipt gate. A changed definition, review interface or price requires a new version and fresh review or a protected reassessment plan.

An optional workflow input `review_run_id` reuses an identical completed review without another provider call. All evidence, signatures, expiry and reconstructed acceptance are rechecked against fresh intake; changed evidence cannot reuse it.

Tests use synthetic organizer records, not scientific approvals. Set `CURVESMASH_TEST_IMAGE` to the pinned Docker digest to include the live isolation check. The current ordinary baselines need no experiments because their argument is analytic.

## Yukon

The repository is public; the challenge is not yet imported. Request owner/import access through [Yukon's challenge form](https://www.yukon.org/create), including the production GitHub App installation and manual promotion permissions for `zac-williamson/curvesmash`. The installed solver CLI has no owner import command. A solver token does not establish importer authorization.

Once access is granted, import the root manifest with both tracks initially closed. Verify actual Yukon baseline jobs, score-artifact ingestion, a permitted candidate submission, protected-path rejection and manual promotion of the exact candidate commit. The platform must protect workflow files before dispatch; a check inside a replaced workflow cannot secure its own credentials. Do not invent successful registration or manually merge Yukon's submission PRs.

GitHub artifacts expire after 30 days. Retain verified local exports and publish release archives containing the candidate, current rules, judgments, execution evidence and scores. Preserve unsuccessful attempts and earlier policies as historical records.
