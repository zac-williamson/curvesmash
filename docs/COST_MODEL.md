# Computation accounting

The score is the submitted **log2(total computation in target-group-operation equivalents)**. Lower is better. Explain the complete calculation in `proof.md`; no cost-ledger file, integer-budget field or intermediate pricing engine is required.

This follows [HashSmash's accounting method](https://github.com/Layr-Labs/hash-smash/blob/main/docs/RESCORING.md): one fixed target operation costs 1, and another 256-bit RAM primitive costs 1/C. HashSmash uses hash compressions; our targets use group operations.

| Target | Reference operation | Fixed C, in word operations |
| --- | --- | ---: |
| secp256k1 | Affine point addition, with exceptional branches covered | 78,037,248 |
| BLS12-381 inversion | Multiplication in the pinned Fp12 basis | 45,839,872 |

These fixed prices are conservative portable reference budgets, not hardware timings or claims that these implementations are fastest. They define units. They are set by the organizer and cannot be changed by a submission. Faster field, group, pairing or lookup algorithms are welcome; justify their actual work. Scores from different tracks are not directly comparable.

Reproduce the prices:

```sh
.venv/bin/python scripts/reference_operation_costs.py
```

For a field of k bits stored in s words, the reference budgets are A=128(s+1) for reduced addition/subtraction, M=k(2A+64)+128(s+1) for fixed-bit modular multiplication, and I=2k(M+64)+128(s+1) for Fermat inversion. The reference point price is I+16M+32A+4096 at k=256,s=1. The reference Fp12 price is 144M+188A+65536 at k=381,s=2. Multiplication uses double-and-add: two reduced additions and bit/control work per bit. Inversion uses binary powering. Affine point formulas and the fixed polynomial reduction establish the group budgets; the baseline arguments spell out their branches and coefficient counts. These allowances include reference control/transfers and may deliberately overestimate them.

Charge total work across processors, including preprocessing, advice construction, random sampling, all trials and failures, sorting, lookup, memory transfers, verification, output and success amplification. A stored answer does not make its search free. Do not charge both a reference operation and its internal instructions. Public profile constants and algorithm design effort are excluded.

Example: if the attack performs H reference operations and W other word operations, the cost is H+W/C, plus any other work. Submit its base-2 logarithm and justify the calculation. A success probability is about the algorithm, not reviewer confidence.

The required success probability is at least 0.39 over uniform production challenges and fresh algorithm coins. Peak memory includes code, advice, tables and scratch. Report memory, preprocessing and advice alongside the computation bound; memory has no scalar contribution or tie-break. Quantum algorithms are outside this classical benchmark.

A supported cost discrepancy must receive a fatal objection and defense/adjudication. Uncertain costs remain visible under the exploratory policy. An accepted submission receives its submitted bound; ordinary judging does not silently optimize it. Organizer-authorized [reassessment](RESCORING.md) preserves the accepted score when scoring rules are unchanged and recalculates it when prices or the cost model change.
