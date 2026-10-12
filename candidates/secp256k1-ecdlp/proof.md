# secp256k1-ecdlp: deterministic generic baseline

Status: ready for independent review; no qualification or emitted score.
This is a conservative accounting control, not a best-known attack claim.
The normative inputs/outputs are those of `production-v2`; `claim.json`
binds that profile and `classical-group-work-v2` by SHA-256. No restricted
challenge distribution, advice, random-oracle premise or quantum operation is used.

## Construction and success

Let p and r be the protected field modulus and subgroup order. Set
b=bit_length(r)=256, L=floor(b/2)=128, m=2^L and h=ceil(r/m).
All table indices/addresses and i*m+j fit 256 bits for these fixed targets.

```text
Use P from the protected profile; input Q. Starting at infinity, store (jP,j)
for j=0..m-1 by repeated affine addition, retaining mP after the final update.
Set D=-(mP) and gamma=Q. Sort the table by (infinity_tag,x,y), tag 1 for infinity and 0 otherwise; use zero
coordinate words for infinity. For i=0..h-1, binary-search gamma; on a match
with j, set a=(i*m+j) mod r, verify [a]P=Q, and return a. Otherwise set
gamma=gamma+D. Reject malformed inputs; exhaust the fixed loops with failure.
```

For every valid Q there is a unique x in [0,r) with Q=[x]P. Write
x=i*m+j with 0<=j<m and 0<=i<h. At giant step i, gamma=[j]P;
the complete table therefore contains a match. Any match yields
[a]P=Q after reduction modulo r. The independent attack-side equality
check accepts it. Infinity gives x=0 and is represented explicitly.

The algorithm succeeds for every valid input: probability 1, hence >=0.39
over the uniform challenge distribution. No randomness, retries or
amplification are needed. A finite worst-case work budget is used; it is
not an expected-runtime or group-operation exponent standing in for total work.

## Word-operation ledger

Integers are little-endian arrays of s=ceil(k/256) limbs, where
k=bit_length(p)=256 and s=1. Each listed cost-model primitive costs one.
Operands of a field operation are canonical integers in [0,p).

| Kernel | Upper bound in word operations |
| --- | ---: |
| Modular addition/subtraction | A=128*(s+1)=256 |
| Base-field multiplication | M=k*(2*A+64)+128*(s+1)=147712 |
| Nonzero base-field inverse | I=2*k*(M+64)+128*(s+1)=75661568 |
| Affine point addition/doubling | C=I+16*M+32*A+4096=78037248 |

For A, zero-extend to s+1 limbs, add/subtract with carry/borrow, compare
against p, and make one conditional correction. Each limb pass needs at
most 16 operations for loads/stores, arithmetic and carry/borrow handling;
allow six passes plus 32*(s+1) for comparison, selection and control.
This accommodates the 257th carry bit even for the 256-bit field.

For M, scan the k bits of the multiplier; conditionally add the running
multiplicand to the accumulator and double it modulo p each iteration.
Two A calls and 64 bit-extraction/loop operations per bit suffice; reserve
128*(s+1) for initialization/output. Inversion uses binary powering by p-2:
at most 2*k multiplications plus 64 operations per bit. All instructions,
including memory transfers, are counted; multiplication/inversion are not
unit-cost primitives.

Point addition uses affine formulas: return the other operand for infinity;
return infinity for opposite points; use slope (v-y)/(u-x) for distinct
x-coordinates or 3*x^2/(2*y) for doubling, with y=0 handled as infinity.
Compute x'=slope^2-x-u and y'=slope*(x-x')-y modulo p. Negation is
(x,-y mod p). A scalar multiplication uses at most 2*b such operations.
C covers every case. Keys have K=3 words and records W=4 words.

Setup reserves 2^24 operations for decoding/constants and the step negation.
Verification/output reserves 4*b*C+2^24: this covers [r]Q and [a]P checks,
curve/encoding checks, scalar reconstruction by shift/add and serialization.

Use bottom-up merge sort with two m-record buffers and exactly L passes.
A lexicographic key comparison costs B=16*K+64; moving a record costs
D=16*W+64. These bounds allow all operand loads, stores, index arithmetic,
comparisons and branches, up to 16 operations per word plus 64 fixed work.
Each merge pass has at most m comparisons and 2*m record moves, with
128*m additional loop work. Thus sorting costs
S=m*L*(B+2*D+128)+4096*L. Binary search performs at most L+1 key
comparisons; V=(L+1)*(B+64)+D+256 covers lookup and the returned record.
No constant-time hashing/table oracle is assumed.

For group-step cost G=C, charge m*(G+D) to build the
baby table, S to sort it, and h*(G+V) for the full giant search. Setup and
verification/output are added in full. The accounting below gives these exact
integer components and their sum T. The reported logarithms are rounded
up to six decimal places; exact integers remain the audit authority.
Preprocessing includes the whole baby table and sorting, with no reuse credit.

Peak memory is 2*m*W*32+2^20 bytes. The two arrays include all keys and
indices. The 1 MiB reserve includes code, public constants, fixed field/point
scratch, loop state and stacks; these use bounded kernels on at most 12
coefficients and 4572-bit exponents. The finite instruction bodies and
scratch fit the reserve; table storage is separate. No table is uncharged
advice. Input/output and all record lifetimes are included. This memory is
astronomical and mandatory for this construction; it is not a practical attack.

## Evidence and comparison

The correctness argument and cost calculation are analytic; no full-size execution is
claimed. Organizer arithmetic fixtures check the exact point/GT convention;
organizer exhaustive finite-group checks exercise table coverage, last-block
handling and modular output recovery. They do not certify production cost,
scientific approval or an executed production break. Heuristic premises: none.

Pollard rho and automorphism-aware methods must be compared under this same cost model before selecting a best-known ECDLP starting score. This package does not implement those optimizations.
Beating this deliberately conservative control alone does not establish
novel cryptanalysis or a weakened hardness assumption.

References: [generic DLP algorithms, HAC section 3.6](https://cacr.uwaterloo.ca/hac/about/chap3.pdf);
[automorphism-aware Pollard rho](https://www.iacr.org/archive/pkc2014/83830154/83830154.pdf).
The needed construction and accounting are given above; review need not
fetch citations to reconstruct them.

## Submitted computation bound

The following integer word-operation bounds follow from the implementation formulas above. They are ordinary proof evidence, not a required submission format.

| Component | Word operations |
| --- | ---: |
| setup | 16777216 |
| baby table | 26554743013579237146153626469005290262239379456 |
| merge sort | 21603846911076541168362727076628100209442816 |
| giant search | 26562555896723741893274745549991923660296348880 |
| verification and output | 79926919168 |

Total word operations: **53138902757214055580596734746073842102688867536**. Preprocessing word operations: **26576346860490313687321989196081918362465599488**. Peak bytes: **87112285931760246646623899502532663181312**; nonuniform advice bytes: 0.

The organizer reference price for this target is 78037248 word operations. Dividing total and preprocessing work by that fixed price gives submitted time_log2 **129.000802** and preprocessing_log2 **128.001176**, rounded upward. Memory_log2_bytes remains **136.000001**. All table access, sorting, failure paths, verification and output costs are included; reference-operation normalization changes units, not the work or algorithm.
