# curvesma.sh

AI-assisted cryptanalysis of **secp256k1 discrete logarithms** and **BLS12-381 pairing inversion**, built for Yukon.

| Track | Challenge | Answer |
| --- | --- | --- |
| `secp256k1-ecdlp` | Given Q=[x]P, for uniform x and fixed standard P | Recover x |
| `bls12-381-invert-g1` | Given uniform z in GT and fixed standard G2 point Q0 | Find P in G1 with e(P,Q0)=z |

Both use full production parameters. There are exactly two tracks and one metric: **log2(total computation in target-group-operation equivalents), lower is better**. Success must be at least 39%. Preprocessing and failed attempts count; memory is reported separately. Explain the calculation in the written argument. No structured cost ledger is required. See the [cost rules](docs/COST_MODEL.md).

Both tracks follow HashSmash's exploratory standard: a concrete, supported claim can score when no fatal flaw survives defense/adjudication. Uncertainty remains in the published review. Acceptance means `plausible_not_refuted`, not proof or a practical break. See the [review rules](docs/EVALUATION.md).

**Participants start at [TASK.md](TASK.md).** It covers the editable surface, local checks, advisory review, experiments and Yukon submissions. Read the [participation terms](docs/legal/TERMS_OF_SERVICE.md) and [privacy notice](docs/legal/PRIVACY_POLICY.md).

The repository is public. Version 2 replaces the original stricter review policy and mandatory ledger with HashSmash-style exploratory review and prose accounting. The version 1 scores remain [historical records](docs/archive/BASELINE_QUALIFICATION_V1.md); they cannot be relabeled in the new units. Fresh version 2 qualification is in progress. The standard baby-step/giant-step candidates are conservative accounting controls, not best-known attack estimates. Yukon import is pending; submissions are not open.

Organizers: [execution and access](docs/EXECUTION.md), [reassessment and history](docs/RESCORING.md), [Yukon proposal](docs/YUKON_PROPOSAL.md).

```sh
bash .yukon/setup.sh
.venv/bin/python scripts/local_tracks.py check secp256k1-ecdlp
.venv/bin/python scripts/local_tracks.py check bls12-381-invert-g1
.venv/bin/python -m unittest discover -s tests -v
```
