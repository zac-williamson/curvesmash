# Reassessment and score history

Ordinary submissions use the submitted computation bound. To reassess existing content after a protected policy or price change, the organizer pins its previous review artifact in `reorg/plan.json`. Unlisted submissions receive ordinary four-role review. This follows HashSmash's distinction between current judging rules and reusable previous reasoning.

The current protected release must contain the pin before dispatch. Candidate packages cannot supply their own history. The intake job fetches only the exact artifact ID from this repository, verifies the ZIP and packet checksums, authenticates the original signed judgments, and rejects different algorithms or mathematical targets. It does not extract or execute artifact files. History is bounded to 32 judgments and 2 MiB.

The review job makes one current-policy reassessment call with the original argument, previous judgments and current rules. Its decision is accepted, rejected or needs evidence. Previous acceptance is not binding. Rejected and incomplete results emit no score.

- Unchanged cost model and reference price: preserve the latest accepted score exactly. No silent tightening.
- Changed cost model or reference price: emit a newly justified computation bound, with the calculation recorded in the reassessment.

The scorer authenticates the reassessment, source packet and scoring-policy identity again. The next artifact carries the previous judgments forward. Clearing the plan changes no historical result and triggers no retrospective evaluations.

## Pin an existing artifact

Download the chosen `curvesmash-review-<track>` artifact ZIP from GitHub. Then run:

```sh
.venv/bin/python scripts/archive_review.py --archive /absolute/path/review.zip --artifact-id ACTUAL_ID
```

The tool verifies the ZIP against GitHub's artifact digest, caches the packet outside Git and prints a proposed plan entry. Review the entry and commit it into the organizer-owned plan before updating `CURVESMASH_TRUSTED_SHA` and dispatching. It never edits the plan or grants approval automatically.

GitHub artifacts expire after 30 days. Publish and retain release archives; an expired or mismatched pinned artifact stops explicitly. Restore a verified artifact through the supported transport or perform fresh ordinary review. Do not substitute a fabricated judgment.

Version 1 baseline results are historical word-operation scores under the retired rigorous policy. Their values must not be relabeled as current group-operation scores. The version 2 baselines require fresh ordinary reviews.
