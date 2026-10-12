# Draft for https://www.yukon.org/create

Not submitted. Name, email, and affiliation must be supplied by the organizer.

## The Problem

Curvesmash (curvesma.sh) is an open AI-assisted cryptanalysis challenge for elliptic-curve discrete logarithms and fixed-argument cryptographic pairing inversion. Its six proposed tracks use unrestricted production parameters: secp256k1 and P-256 ECDLP; inversion into G1 and G2 for Ethereum BN254 and BLS12-381. Each track minimizes log2 expected total classical computation for a single target at a fixed success requirement. Memory, preprocessing, heuristic assumptions, and evidence are public supplementary metrics. Small and restricted instances are supporting experiments, not production leaderboard targets. The aim is to identify defensible reductions in attack cost against common hardness assumptions.

## The Verifier

We propose deterministic intake and independent point/pairing checks, followed by scoped experiments in an isolated credential-free executor and cryptanalytic review of full-size resource and success claims. Accepted scores are derived from a protected, versioned cost model, bound to the exact package, parameters, evidence, and review configuration. Executed results and extrapolated cost claims remain distinct. AI screening and expert acceptance are recorded separately, and promotion requires owner review. Full-size attacks need not be executed when infeasible; their complexity arguments and assumptions must be supported. This infrastructure is currently a prelaunch scaffold, not a completed verifier.

## Yukon integration request

We would like to confirm the current production owner/import workflow for a schema-v2 multi-track repository, closed baseline qualification and manual promotion, review-provider integration, research Discussions, and whether a branded challenge page/domain can use the same published result infrastructure as HashSmash.

## Link

[zac-williamson/curvesmash](https://github.com/zac-williamson/curvesmash) — a private prelaunch starter. Yukon will need explicit repository access before reviewing it. The verifier and scientific qualifications remain to be implemented.
