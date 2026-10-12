# curvesma.sh

AI-assisted research into elliptic-curve discrete logarithms and pairing inversion, built for Yukon. Owner: [zac-williamson](https://github.com/zac-williamson).

## Two tracks

| Track | Challenge | Required output |
| --- | --- | --- |
| `secp256k1-ecdlp` | Fixed generator P; Q = [x]P for uniform x in Z/rZ | x such that [x]P = Q |
| `bls12-381-invert-g1` | Fixed G2 generator Q0; uniform z in GT | P in G1 such that e(P,Q0) = z |

Both use full production parameters. Exact parameters, encodings and the pinned pairing convention are in [production-v1](target-profiles/production-v1.json). Small or restricted instances provide supporting evidence only.

## One metric

**log₂ total classical attack work budget; lower is better.** The algorithm must return a valid result within that budget with probability at least 39% over uniform challenges and fresh algorithm randomness. Charge preprocessing, failed trials, verification and amplification. Publish memory costs and assumptions alongside the score.

The [cost model](cost-models/classical-word-ram-v1.json) uses HashSmash's 256-bit word-RAM primitives and success threshold. Each primitive costs one word-operation; higher arithmetic must supply a complete implementation ledger. Scores represent reviewed full-size complexity claims; experiments are separate evidence. Independent scientific review is pending.

## Build sequence

1. Review the versioned target/cost specifications and qualify a fully accounted baseline for each track. A generic control is eligible; label it honestly and keep best-known attack comparisons separate.
2. Implement independent mathematical checks, isolated experiments, and cryptanalysis/cost review. Bind each score to its submission, definitions, and evidence; require manual promotion.
3. Register with Yukon while submissions remain closed, then verify baseline runs and the review/promotion lifecycle.
4. Connect curvesma.sh to a two-row results page with baseline cost, best accepted cost, and evidence links.

Use [HashSmash's builder guide](https://github.com/Layr-Labs/hash-smash/blob/main/docs/BUILDER_GUIDE.md) as the evaluation reference. The [Yukon proposal](docs/YUKON_PROPOSAL.md) is drafted and has not been submitted.

## Current status

Private prelaunch project. Both deterministic baby-step/giant-step baselines passed the live AI reviews and emitted verified scores on October 12, 2026, after organizer approval of the scoring rules. The secp256k1 score is **155.218461**; BLS12-381 inversion is **153.944862**. These are conservative accounting controls with success probability 1, not best-known attack estimates or practical breaks. See the [qualification record](docs/BASELINE_QUALIFICATION.md) for the exact release, runs and evidence. Independent human cryptanalytic validation, judge calibration, Yukon import and the website remain outstanding. Submissions remain closed.

- [secp256k1 baseline](candidates/secp256k1-ecdlp/README.md)
- [BLS12-381 inversion baseline](candidates/bls12-381-invert-g1/README.md)

Install the hash-locked organizer environment, then run the checks:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
bash .yukon/setup.sh
.venv/bin/python -m unittest discover -s tests -v
```

The manifest binds each track to its separated GitHub Actions workflow. See [EXECUTION.md](docs/EXECUTION.md) for the pinned release, credentials and artifact contract. Scores remain gated on actual qualification. Passing local checks establishes neither scientific qualification nor Yukon readiness. See [EVALUATION.md](docs/EVALUATION.md) for the complete review and scoring protocol.
