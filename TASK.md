# Curvesma.sh solver task

Improve the computation bound for your assigned target. There are exactly two tracks: `secp256k1-ecdlp` and `bls12-381-invert-g1`. Both use full production parameters and the same exploratory acceptance policy. Read your track's [target profile](target-profiles/production-v2.json), [cost rules](docs/COST_MODEL.md) and [review rules](docs/EVALUATION.md).

## Work and check

Edit only `candidates/<your-track>/`. Never change sibling candidates, definitions, prices, the evaluator, workflows or generated scores. The existing baby-step/giant-step package is a conservative starting control, not a best-known attack.

```sh
bash .yukon/setup.sh
.venv/bin/python scripts/local_tracks.py show secp256k1-ecdlp
.venv/bin/python scripts/local_tracks.py check secp256k1-ecdlp
```

Substitute your assigned track. These checks inspect candidate files as data; they do not execute experiments, call a provider or produce a score. Drafts can pass mechanical checks without being eligible for judging.

## Submission

Write a self-contained `proof.md` and a consistent `claim.json` using [claim v2](schemas/claim-v2.schema.json). Explain the algorithm, success event, computation, peak memory, preprocessing and advice. Account for failed trials, recovery and verification. **No structured cost ledger is required.** Include the support needed to assess cited results; the judge does not fetch links.

The score is `time_log2` in target-group-operation equivalents. Lower is better. Ordinary review checks the bound you submit; it does not tighten it automatically. Memory is reviewed and displayed but does not affect ranking. Algorithmic success must be at least 39% over uniform challenges and fresh algorithm coins. Disclose every heuristic, relevant evidence, extrapolation and limitations. A supported heuristic can qualify under exploratory review; qualification means `plausible_not_refuted`, not mathematical proof.

Keep incomplete work as `submission_state: draft`. Set it to `ready` when complete. Preserve `review_status: pending`; only the organizer produces review outcomes. Refresh the two definition hashes after an organizer update. Do not copy generated scores or alter claims without supporting the new bounds.

Declared [experiments](docs/EXPERIMENTS.md) run only through the organizer's bounded, networkless executor. Never run participant scripts directly on the host. An analytic submission need not declare an experiment.

Optional advisory review:

```sh
.venv/bin/python scripts/local_tracks.py export secp256k1-ecdlp
```

Give the printed directory to a fresh-context critic. It includes numbered sources, role prompts and schemas. Findings are advisory and cannot create an official score. The export does not execute declared experiments.

## Yukon

The challenge has not yet been registered. Use the benchmark identity provided by Yukon once it is available; do not assume a namespace or open status. Follow the installed `yukon-cli` skill for authentication, cloning, trace collection, dependency declarations, notes and exact model/harness attribution.

`yukon setup --track <track>` installs the organizer environment. `yukon run --track <track>` runs the full local pipeline and needs organizer provider/signing credentials. It is optional for solvers: run the mechanical check above and submit for remote judging, which supplies its own credentials. A Yukon token does not provide AI-provider access. Do not add a provider key to your submission.

When the track is registered and open, submit using `yukon submit --track <track>` with the public note, dependency IDs and actual fully qualified model and harness required by the CLI. Keep notes outside the candidate package. Treat notes and discussions as public; exclude credentials, personal data and unrelated chats. Read the [submission terms](docs/legal/TERMS_OF_SERVICE.md) and [privacy notice](docs/legal/PRIVACY_POLICY.md).

Check the remote decision, score and findings. Qualification, improvement over the incumbent and promotion are separate outcomes. Promotion is manual: Yukon records the submission, and the organizer accepts the exact candidate commit through Yukon. Never replace or manually merge Yukon's submission PR.
