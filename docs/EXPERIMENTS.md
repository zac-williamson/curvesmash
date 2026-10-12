# Declared experiments

Experiments are supporting evidence, not a third track. An analytic argument need not execute an infeasible production attack.

An optional claim field declares `experiment: {entrypoint: "experiments/attack.py", trials: 1}`. The entrypoint must be inside the selected candidate directory. Up to eight trials may run. Each trial gets a fresh container with the immutable candidate snapshot, no network, read-only root/submission, an unprivileged user, bounded CPU/memory/PIDs/output and 30 seconds of execution time. The organizer controls all container settings; participant commands are never executed on the host.

For an attack trial, stdin is one JSON challenge: `{Q: ...}` for secp256k1 or `{z: ...}` for pairing inversion. Output is one JSON answer: `{x: ...}` or `{P: ...}` using the target profile's exact canonical encoding. The organizer independently checks the result and records success or failure. Failed attack trials are evidence, not infrastructure failures. Invalid output schemas, timeouts and process failures stop the experiment.

The review job attests the same-run execution artifact after rechecking its binding and output equations. Reviewers examine the inert source and results. A finite successful run does not establish a production success probability or expected cost, and participant counters do not determine the score.

Never run candidate Python directly, add a replacement executor, forward host secrets or mount private directories to obtain evidence. Participant checks and advisory exports do not execute experiments.

For finite heuristic or component studies, declare `kind: "analysis"`. Stdin contains the track, trial index and a fresh 256-bit reproducibility seed. Output is `{counts: [{id: "relation", tested: 1000, satisfied: 42}]}` with bounded integer counts. These are program-reported counts, not independently verified attack successes. The runner records their source and execution; the experiments reviewer assesses the statistical design, counter integrity, relevance and extrapolation. Analysis reports cannot assert production correctness through the attack verifier.
