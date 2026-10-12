# Curvesmash / curvesma.sh

Prelaunch starter for a Yukon research challenge on unrestricted production elliptic-curve discrete logarithms and fixed-argument pairing inversion, owned by [zac-williamson](https://github.com/zac-williamson). This challenge is unregistered and not open for submissions. The mathematical profiles, cost model, baselines, execution system, and scientific review still require implementation and qualification. No scores are generated.

## Agreed competition

One headline metric per fixed target: `time_log2 = log2(expected total charged classical computation)` for a single target, with algorithmic success probability at least 0.9 over the specified challenge distribution and algorithm randomness. Lower is better. This is a proposed contract requiring scientific signoff; the exact operation prices remain unresolved. Memory, preprocessing, assumptions, and evidence are published alongside the scalar. Success probability is not reviewer confidence.

| Track | Production target | Required output |
| --- | --- | --- |
| secp256k1-ecdlp-exploratory | Uniform scalar in the prime-order subgroup | Scalar x with [x]P = Q |
| p256-ecdlp-exploratory | Uniform scalar in the prime-order subgroup | Scalar x with [x]P = Q |
| bn254-invert-g1-exploratory | Ethereum alt_bn128 parameters, fixed generator in G2, uniform z in GT | P in G1 with e(P,Q0) = z |
| bn254-invert-g2-exploratory | Ethereum alt_bn128 parameters, fixed generator in G1, uniform z in GT | Q in G2 with e(P0,Q) = z |
| bls12-381-invert-g1-exploratory | BLS12-381, fixed generator in G2, uniform z in GT | P in G1 with e(P,Q0) = z |
| bls12-381-invert-g2-exploratory | BLS12-381, fixed generator in G1, uniform z in GT | Q in G2 with e(P0,Q) = z |

Pairing maps, generators, finite-field towers, encodings, and independent verifier versions must be pinned before qualification. Curve names or pairing-check EIPs alone do not specify a pairing-output convention. Changing the fixed argument to an arbitrary supplied point would define a different problem and require a separate reviewed version.

Restricted scalars and small curves are supporting experiments only. They do not produce headline production scores. A reviewed full-size complexity claim can be scored without executing an infeasible full attack; executed finite checks and extrapolated claims must remain distinguishable. A solved instance, review acceptance, and a proof of general attack complexity are different evidence.

## Current deliverables

- Root schema-v2 manifest draft with six disjoint candidate directories and manual promotion.
- Protected target and cost-model drafts, with unresolved scientific items explicitly listed.
- Non-executing prelaunch checker and offline tests of important rejection gates.
- Launch plan and a draft for Yukon's public challenge proposal form.

The checker validates this starter's local consistency, not acceptance by Yukon's manifest validator or any cryptanalytic result. The manifest has no production runner or workflows yet. The checker never executes candidates, calls model providers, imports a challenge, or writes a score. `--require-ready` deliberately fails even if draft status fields are changed, because the production evaluation pipeline has not been implemented.

## Local verification

```sh
python3 scripts/prelaunch.py
python3 -m unittest discover -s tests -v
python3 scripts/prelaunch.py --require-ready
```

The first two commands should pass. The last must fail with the unresolved readiness requirements and emit no score.

## Launch sequence

1. Review the fixed production-target contract with ECDLP and pairing cryptographers; lock parameters, conventions, success model, and operation prices.
2. Implement independent algebraic checks, evidence intake, immutable package binding, the isolated experiment executor, and scientific review. Validate them with genuine and deliberately flawed organizer fixtures.
3. Author and qualify a complete baseline package for each track. Use appropriate Pollard/endomorphism methods for ECDLP and compare pairing inversion against target-group DLP plus scalar multiplication, including applicable finite-field attacks. Do not insert nominal security numbers as baseline scores.
4. Configure the appropriate Yukon production App for `zac-williamson/curvesmash` and separate review-provider access, and register the repository through the current supported Yukon owner workflow. Keep admission closed during integration.
5. Verify exact-source validation, protected-path rejection, failed-review/no-score behavior, manual owner acceptance, and preservation of sibling tracks. Record commit, package/configuration fingerprints, execution evidence, review outcomes, and actual service IDs.
6. Release the results page, domain, solver instructions, review committee, and opening decision after the integration is verified.

The installed Yukon CLI currently exposes solver operations rather than a challenge-creation command. The public create route is https://www.yukon.org/create, a proposal form; registration and a bespoke branded page need a confirmed owner workflow. Do not assume `yukon init` exists based on the marketing illustration.

## Sources and reuse

This is an original scaffold informed by public contracts, not a copy of HashSmash's implementation. Before reusing upstream code, resolve its license or obtain permission and record a pinned upstream commit. Its security properties and scientific calibration do not transfer automatically.

- [HashSmash builder guide](https://github.com/Layr-Labs/hash-smash/blob/main/docs/BUILDER_GUIDE.md)
- [HashSmash review contract](https://github.com/Layr-Labs/hash-smash/blob/main/docs/JUDGE_LANES.md)
- [HashSmash production setup](https://github.com/Layr-Labs/hash-smash/blob/main/docs/YUKON_PROD_SETUP.md)
- [HashSmash qualification](https://github.com/Layr-Labs/hash-smash/blob/main/docs/CANDIDATE_QUALIFICATION.md)
- [Aspects of Pairing Inversion](https://eprint.iacr.org/2007/256)
- [Updating key size estimations for pairings](https://eprint.iacr.org/2017/334)

Repository owner: `zac-williamson`. Repository license, domain control, reviewer appointments, provider choice, and running budget remain organizer decisions.
