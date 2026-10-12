# curvesma.sh

AI-assisted research into elliptic-curve discrete logarithms and pairing inversion, built for Yukon. Owner: [zac-williamson](https://github.com/zac-williamson).

## Two tracks

| Track | Challenge | Required output |
| --- | --- | --- |
| `secp256k1-ecdlp` | Fixed generator P; Q = [x]P for uniform x in Z/rZ | x such that [x]P = Q |
| `bls12-381-invert-g1` | Fixed G2 generator Q0; uniform z in GT | P in G1 such that e(P,Q0) = z |

Both use full production parameters. Small or restricted instances provide supporting evidence only.

## One metric

**log₂ expected total classical attack computation; lower is better.** The draft requires at least 90% success over random challenges and algorithm randomness, and charges preprocessing, failed trials, verification, and amplification. Publish memory costs and assumptions alongside the score.

The success convention and operation prices need scientific approval. Scores will represent reviewed full-size attack-cost claims. Executed experiments must be identified separately.

## Build sequence

1. Lock exact parameters, pairing conventions, encodings, and the computation model. Review a best-known baseline for each track.
2. Implement independent mathematical checks, isolated experiments, and cryptanalysis/cost review. Bind each score to its submission, definitions, and evidence; require manual promotion.
3. Register with Yukon while submissions remain closed, then verify baseline runs and the review/promotion lifecycle.
4. Connect curvesma.sh to a two-row results page with baseline cost, best accepted cost, and evidence links.

Use [HashSmash's builder guide](https://github.com/Layr-Labs/hash-smash/blob/main/docs/BUILDER_GUIDE.md) as the evaluation reference. The [Yukon proposal](docs/YUKON_PROPOSAL.md) is drafted and has not been submitted.

## Current status

Private prelaunch starter. The target and cost definitions are drafts; baselines, attack verification, isolated execution, scientific review, Yukon integration, and the website remain to be built. The manifest has no production runner. Nothing is open or scored.

The local checker checks draft consistency and never executes submissions or writes scores:

```sh
bash .yukon/setup.sh
python3 -m unittest discover -s tests -v
```

`python3 scripts/prelaunch.py --require-ready` deliberately fails until the evaluation system is implemented. Passing local checks establishes neither scientific qualification nor Yukon readiness.
