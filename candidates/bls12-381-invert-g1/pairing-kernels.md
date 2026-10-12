# Complete pairing kernels and operation bound

This appendix supplies the formulas omitted from the first review package.
It implements the exact map pinned in `production-v1`, using the formulas
of py_ecc 8.0.0 at commit `04151f01f59f902ab932a51e0ca0ebce3883fc51`:
`optimized_bls12_381/optimized_curve.py` (`add`, `double`, `twist`) and
`optimized_bls12_381/optimized_pairing.py` (`linefunc`, `miller_loop`,
`cast_point_to_fq12`, `pairing`). The profile binds those files by hash.
The needed formulas are reproduced below; reviewers need not fetch sources.
The arithmetic implementation is the word-RAM construction in `proof.md`,
not the Python interpreter. The py_ecc MIT notice is in `py-ecc-LICENSE.txt`.

Let A, M, E and k have the meanings in `proof.md`. In particular,
E=144*M+188*A+65536=45,839,872. Every field multiplication below, including
multiplication by a small integer constant, is charged as a full product.
Fp2 uses u^2=-1: (a+bu)(c+du)=(ac-bd)+(ad+bc)u. This needs four M
and two A calls. Fp2 addition/subtraction needs two A calls. These calls,
including at most 4096 additional word operations for argument copying,
addressing and control, cost less than E. No Fp2 inversion is used below.
Fp12 multiplication costs E by the polynomial reduction already derived;
Fp12 addition/subtraction costs at most 12*A+4096, also below E.

## Projective point operations over Fp2

Coordinates (x,y,z) represent (x/z,y/z); z=0 represents infinity.
The following are straight-line formulas in Fp2.

For doubling:

```text
W = 3*x*x
S = y*z
B = x*y*S
H = W*W - 8*B
S2 = S*S
X = 2*H*S
Y = W*(4*B-H) - 8*y*y*S2
Z = 8*S*S2
return (X,Y,Z)
```

This has 17 multiplications (constants included) and three subtractions.
For addition of (x1,y1,z1) and (x2,y2,z2):

```text
if z1=0: return (x2,y2,z2)
if z2=0: return (x1,y1,z1)
U1=y2*z1; U2=y1*z2; V1=x2*z1; V2=x1*z2
if V1=V2:
    if U1=U2: return double(x1,y1,z1)
    else: return (1,1,0)
U=U1-U2; V=V1-V2
Vsq=V*V; VsqV2=Vsq*V2; Vcube=V*Vsq; W=z1*z2
A0=U*U*W - Vcube - 2*VsqV2
X=V*A0
Y=U*(VsqV2-A0) - Vcube*U2
Z=Vcube*W
return (X,Y,Z)
```

The ordinary branch has 15 products and six subtractions. The doubling
branch has the four preliminary products plus the doubling kernel: 21
products and three subtractions. Charge at most 32 arithmetic calls for
any branch. Equality tests compare the four limbs of an Fp2 value.
Argument/result copying, these tests and branch/loop control together are
bounded by 65536 word operations, less than E. Thus 64*E bounds either
point operation, including all exceptional cases, loads and stores.

## Twist and base-point embedding

The flat Fp12 basis satisfies w^12=2*w^6-2 and u=w^6-1, so u^2=-1.
For each Fp2 coordinate t=a+bu compute c=a-b. The twist is:

```text
nx=(ax-bx)*w + bx*w^7
ny=(ay-by)   + by*w^6
nz=(az-bz)*w^3 + bz*w^9
return (nx,ny,nz)
```

All omitted coefficients are zero. This is exactly the pinned `twist`
coefficient placement. It needs three A calls and construction/copying
of three 24-word Fp12 arrays. At most 65536 word operations cover all array
initialization, coefficient loads/stores and control; three A plus this
reserve is below 4*E. Charge 64*E. To cast a base-field projective P into
Fp12, put each coordinate in coefficient zero, setting coefficients
1..11 to zero. The same 65536 reserve bounds this one-time embedding.

## Rational line evaluation over Fp12

For projective points R1=(x1,y1,z1), R2=(x2,y2,z2) and evaluation point
T=(xt,yt,zt), compute numerator n and denominator d without division:

```text
mn=y2*z1-y1*z2
md=x2*z1-x1*z2
if md != 0:
    n=mn*(xt*z1-x1*zt) - md*(yt*z1-y1*zt)
    d=md*zt*z1
elif mn=0:
    mn=3*x1*x1
    md=2*y1*z1
    n=mn*(xt*z1-x1*zt) - md*(yt*z1-y1*zt)
    d=md*zt*z1
else:
    n=xt*z1-x1*zt
    d=z1*zt
return (n,d)
```

Counting the preliminary mn and md in every branch, the ordinary branch
needs 12 products and five subtractions, the tangent branch 16 products
and five subtractions, and the vertical branch seven products and three
subtractions. Fp12 zero tests inspect 24 limbs each. A 65536-word reserve
bounds coordinate movement, tests and control, less than E. Charge 64*E
for a complete line call. Multiplication by 2 or 3 is not free.

## Exact Miller schedule and wrapper

The positive loop parameter is 0xd201000000010000, 64 bits long. Initialize
R=Q0 and fnum=fden=1; compute twist(Q0) and cast(P). Process bits 62..0
in descending order, exactly as the reference's `pseudo_binary_encoding[62::-1]`:

```text
(n,d)=line(twist(R),twist(R),cast(P))
fnum=fnum*fnum*n; fden=fden*fden*d
R=double(R); twistR=twist(R)
if bit=1:
    (n,d)=line(twistR,twist(Q0),cast(P))
    fnum=fnum*n; fden=fden*d
    R=add(R,Q0); twistR=twist(R)
```

There are 63 doubling substeps and at most 63 addition substeps. Each
substep costs at most:

| Component | Charged E units | Justification |
| --- | ---: | --- |
| Fp2 point operation | 64 | Counts and exceptional branches above |
| Fp12 line evaluation | 64 | At most 16 products, five subtractions and bounded movement |
| Twist | 64 | Explicit coefficient placement above |
| Accumulators | 16 | Four products for doubling or two for addition, plus copying |
| Schedule/control | 1 | At most 65536 word operations |
| Total | 209 | Strictly less than the existing 512-E allowance |

The two unused slots in 128*512*E cover initialization/wrapper and final
quotient multiplication. Curve validation uses y^2*z=x^3+b*z^3 in the
appropriate field, at most eight products and one addition per point,
with zero-z tests. This is the pinned project's `is_on_curve` condition.
Initialization, validation of both points, embedding, initial twist,
constant/accumulator construction, quotient multiplication and output
copying together fit 256*E plus 65536 word operations, below these two
slots. If P or Q is infinity the wrapper returns 1, as the pinned map does.

For nonidentity valid inputs the loop's Fp2 points are [n]Q0 with
0<n<=0xd201000000010000<r. They never reach infinity or a point of order
two. An addition step cannot have R=-Q0: its positive scalar n is far
below r-1. Consequently the projective z values and tangent/ordinary line
denominators in this schedule are nonzero. With cast(P).z=1, fden is a
product of nonzero factors. The final inverse below is well defined.

Compute f=fnum*(fden^(p^12-2)), then return f^((p^12-1)/r).
These are the reference quotient and its exact final exponent; Fermat
inversion changes the implementation, not the pairing value. Each exponent
has at most 12*k bits. Binary powering takes at most 24*k products per
exponent, at most 48*k in total. The final quotient multiplication is
already in the two wrapper slots; no product is omitted. Scalar exponent
bits are scanned once; at most 64 operations per bit plus 4096 per power
cover index/control and accumulator initialization, below 2^26.

The bound 2^26 also covers constructing the exponents and decoding. Use
12 unsigned bit-serial integer products to form p^12, with at most 381
multiplier bits and 19 limbs including the extra carry limb. A product bit
uses one limb pass to double the running multiplicand and one to add it
to the accumulator when that bit is set. Each pass takes at most 16
operations per limb, including carry handling, loads and stores. Reserve 128
operations per limb per bit, giving at most 12*381*19*128=11,119,104.
Long division by r requires at most 4572 shift/compare/subtract stages;
Each stage uses a remainder-shift pass, a comparison pass and a conditional
subtraction pass, at most 16 operations per limb per pass, plus bit/control
work. Reserving 128*19 operations per stage costs at most 11,119,104. Fixed decoding,
constant assembly and both powering control loops fit the remaining
44,870,656 operations. These are ordinary limb passes, not integer
multiplication/division oracles.

Therefore the unchanged bound
J=(128*512+48*k)*E+2^26 fully charges this exact pairing map. Its constant
is conservative and its complete contribution remains in setup and
verification in `ledger.json`. No free pairing or unstated cost heuristic
is used. The appendix changes the justification, not the claimed budget.
