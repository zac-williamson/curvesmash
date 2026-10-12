# Yukon proposal

Draft for [Yukon's challenge form](https://www.yukon.org/create). Not submitted. Organizer contact details still need to be supplied.

## Problem

Curvesma.sh is an AI-assisted cryptanalysis challenge with two production targets: secp256k1 discrete logarithms and BLS12-381 pairing inversion into G1 with a fixed G2 generator. Both minimize log₂ classical word-operation work budget with at least 39% success. Submissions must support their full-size complexity claims; smaller experiments supply evidence.

## Evaluation

The evaluator is implemented: mathematical output checks, isolated experiments, authenticated cryptanalysis/cost review and evidence-bound scoring. Scores include preprocessing and require a qualifying review; owner approval is required before promotion. Both initial baselines have passed live AI reviews and emitted verified scores: 155.218461 for secp256k1 and 153.944862 for BLS12-381 inversion. They are fully accounted generic controls, not practical attacks or best-known estimates. See the [qualification record](BASELINE_QUALIFICATION.md). Independent human cryptanalytic validation, judge calibration and Yukon integration remain outstanding. Local and Linux CI checks pass.

## Integration

Please confirm the production registration workflow, repository App access, review-provider setup, and hosting a branded results page at curvesma.sh. Integration will begin with submissions closed.

Repository: [zac-williamson/curvesmash](https://github.com/zac-williamson/curvesmash), currently private.
