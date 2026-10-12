# bls12-381-invert-g1: deterministic generic baseline

Status: ready for independent review; no qualification or emitted score.
This is a conservative accounting control, not a best-known attack claim.
The normative inputs/outputs are those of `production-v1`; `claim.json`
binds that profile and `classical-word-ram-v1` by SHA-256. No restricted
challenge distribution, advice, random-oracle premise or quantum operation is used.

## Construction and success

Let p and r be the protected field modulus and subgroup order. Set
b=bit_length(r)=255, L=floor(b/2)=127, m=2^L and h=ceil(r/m).
All table indices/addresses and i*m+j fit 256 bits for these fixed targets.

```text
Compute g=e(P0,Q0) with the exact protected pairing convention; input z.
Starting at 1, store (g^j,j) for j=0..m-1 by repeated Fp12 multiplication,
retaining g^m after the final update. Set D=(g^m)^(r-1) and gamma=z.
Sort by the 24-word canonical coefficient key. For i=0..h-1, binary-search
gamma; on a match with j, set a=(i*m+j) mod r, compute P=[a]P0, verify
[r]P=infinity and e(P,Q0)=z, and return P. Otherwise set gamma=gamma*D.
Check the input encoding and z!=0, z^r=1 before searching; reject invalid input.
```

The pinned nondegenerate pairing maps P0,Q0 to a nonidentity g in GT.
Since GT has prime order r, g generates GT. For every valid z there is a
unique x in [0,r) with z=g^x. Write x=i*m+j, 0<=j<m, 0<=i<h.
Then z*(g^(-m))^i=g^j, so a table match exists. Any match gives a=x mod r,
and bilinearity yields e([a]P0,Q0)=g^a=z. The output is in G1;
identity z=1 produces infinity. Full pairing equality is checked.

The algorithm succeeds for every valid input: probability 1, hence >=0.39
over the uniform challenge distribution. No randomness, retries or
amplification are needed. A finite worst-case work budget is used; it is
not an expected-runtime or group-operation exponent standing in for total work.

## Word-operation ledger

Integers are little-endian arrays of s=ceil(k/256) limbs, where
k=bit_length(p)=381 and s=2. Each listed cost-model primitive costs one.
Operands of a field operation are canonical integers in [0,p).

| Kernel | Upper bound in word operations |
| --- | ---: |
| Modular addition/subtraction | A=128*(s+1)=384 |
| Base-field multiplication | M=k*(2*A+64)+128*(s+1)=317376 |
| Nonzero base-field inverse | I=2*k*(M+64)+128*(s+1)=241889664 |
| Affine point addition/doubling | C=I+16*M+32*A+4096=246984064 |

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

Fp12 coefficients use two 256-bit limbs each. Multiply by 144 base-field
products and at most 144 coefficient additions, then eliminate degrees
22 down to 12 using w^12=2*w^6-2. Each of the 11 eliminations needs at
most four modular additions/subtractions. E=144*M+188*A+65536 includes
coefficient copying, addressing and loop control. Addition in Fp12 also costs
less than E. Binary powering of a d-bit exponent takes at most 2*d
multiplications and at most 64*d control operations.

The paired reference Miller loop has 63 bit iterations and at most one
extra addition per iteration. Charge 128 substeps of 512 Fp12-sized
arithmetic operations each: the projective point, line, twist and accumulator
formulas fit this allowance without inversion inside the loop. Per substep,
allow 64 Fp2 operations for point arithmetic, 64 Fp12 operations for the
line, 64 base/Fp2 operations for twisting, 16 Fp12 accumulator operations,
and 65536 word operations for coefficient movement and control. Fp2
multiplication needs at most four M calls and four A calls, below E;
all other listed Fp2 operations also fit E. The control allowance is below E,
so this subtotal is below 512*E. Replace its
single Fp12 quotient inversion with powering by p^12-2. Charge a further
24*k products for that inversion and 24*k for final exponentiation.
The 2^26 allowance covers exponent construction, decoding and control.
Compute p^12 with 12 bit-serial integer products (at most 381 bits in the
multiplier, 18 limbs in the accumulator) and divide by r using at most
4572 shift/subtract stages. Even allowing 128 operations per limb pass,
the products and division fit this allowance.
Thus J=(128*512+48*k)*E+2^26 bounds one complete pinned pairing.
This describes a word-RAM implementation of that map, not Python wall time.

Setup is J+2*b*E+2^24: compute g, invert g^m by exponent r-1, and decode.
Verification/output is J+8*b*C+4*b*E+2^24, allowing the final pairing,
input GT subgroup/power checks, output recovery/subgroup checks and
serialization. Base-field affine formulas and binary scalar multiplication
use C: for distinct x-coordinates use slope (v-y)/(u-x); for doubling use
3*x^2/(2*y); return infinity for opposite points or y=0 doubling. Handle
infinity before division. Compute x'=slope^2-x-u and
y'=slope*(x-x')-y. These formulas need one I and fewer than 16 M and
32 A calls, with 4096 operations for movement, tests and control. Binary
scalar multiplication takes at most 2*b point operations; at most four
scalar multiplications are allowed in verification/output.
Keys have K=24 words and records W=25 words, including the exponent j.

Use bottom-up merge sort with two m-record buffers and exactly L passes.
A lexicographic key comparison costs B=16*K+64; moving a record costs
D=16*W+64. These bounds allow all operand loads, stores, index arithmetic,
comparisons and branches, up to 16 operations per word plus 64 fixed work.
Each merge pass has at most m comparisons and 2*m record moves, with
128*m additional loop work. Thus sorting costs
S=m*L*(B+2*D+128)+4096*L. Binary search performs at most L+1 key
comparisons; V=(L+1)*(B+64)+D+256 covers lookup and the returned record.
No constant-time hashing/table oracle is assumed.

For group-step cost G=E, charge m*(G+D) to build the
baby table, S to sort it, and h*(G+V) for the full giant search. Setup and
verification/output are added in full. `ledger.json` gives these exact
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

The correctness argument and ledger are analytic; no full-size execution is
claimed. Organizer arithmetic fixtures check the exact point/GT convention;
organizer exhaustive finite-group checks exercise table coverage, last-block
handling and modular output recovery. They do not certify production cost,
scientific approval or an executed production break. Heuristic premises: none.

Finite-field DLP methods, including applicable NFS/TNFS variants with all relation collection, linear algebra and descent charged, must be compared before selecting a best-known pairing-inversion starting score. The generic square-root construction is not a finite-field security estimate.
Beating this deliberately conservative control alone does not establish
novel cryptanalysis or a weakened hardness assumption.

References: [generic DLP algorithms, HAC section 3.6](https://cacr.uwaterloo.ca/hac/about/chap3.pdf);
[pairing key-size analysis](https://eprint.iacr.org/2017/334).
The needed construction and accounting are given above; review need not
fetch citations to reconstruct them.
