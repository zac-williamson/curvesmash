# Yukon proposal

Draft for [Yukon's challenge form](https://www.yukon.org/create). Not submitted. Organizer contact details still need to be supplied.

## Problem

Curvesma.sh is an AI-assisted cryptanalysis challenge with two production targets: secp256k1 discrete logarithms and BLS12-381 pairing inversion into G1 with a fixed G2 generator. Both minimize log₂ classical word-operation work budget with at least 39% success. Submissions must support their full-size complexity claims; smaller experiments supply evidence.

## Evaluation

The evaluator is implemented: mathematical output checks, isolated experiments, authenticated cryptanalysis/cost review and evidence-bound scoring. Scores include preprocessing and require a qualifying review; owner approval is required before promotion. These are reviewed full-size complexity claims, not claims of practical full-size attack execution. Versioned target/cost specifications and two conservative generic baseline proposals are written. Scientific review, judge calibration, starting baseline qualification and production deployment remain outstanding. The initial baselines need not be best-known attacks; generic controls require full accounting and qualifying review and will be labeled accordingly. Local and Linux CI checks pass; no baseline has been qualified or scored.

## Integration

Please confirm the production registration workflow, repository App access, review-provider setup, and hosting a branded results page at curvesma.sh. Integration will begin with submissions closed.

Repository: [zac-williamson/curvesmash](https://github.com/zac-williamson/curvesmash), currently private.
