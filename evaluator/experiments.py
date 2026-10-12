"""Credential-free, bounded container execution with organizer output verification."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import selectors
import secrets
import subprocess
import tempfile
import time
import uuid

from .common import canonical, digest, exact, integer, number, require, parse, sha, HEX, text
from .review import sign, verify
from .verifier import Verifier
from .intake import check_evidence


def docker_command(image, directory, entrypoint, name, policy):
    require(type(image) is str and re.fullmatch(r"[A-Za-z0-9./:_-]+@sha256:[0-9a-f]{64}", image),
            "Organizer must pin an immutable experiment image digest")
    integer(policy["experiment_timeout_seconds"], 1, 30)
    integer(policy["experiment_memory_bytes"], 32*1024*1024, 512*1024*1024)
    integer(policy["experiment_output_bytes"], 1024, 65536)
    # Entrypoint, privileges, resources and runtime are organizer choices, never candidate options.
    return ["docker", "run", "--pull=never", "--rm", "-i", "--name", name,
        "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--pids-limit=64", "--cpus=1", f"--memory={policy['experiment_memory_bytes']}",
        f"--memory-swap={policy['experiment_memory_bytes']}", "--user=65534:65534",
        "--ulimit=nofile=64:64", "--ulimit=fsize=65536:65536",
        "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16777216", "--workdir=/tmp",
        "--mount", f"type=bind,source={directory},target=/candidate,readonly",
        "--entrypoint=/usr/local/bin/python", image, "/candidate/"+entrypoint]


def bounded_process(command, stdin, timeout, limit):
    """Drain both pipes under one byte cap; enforce elapsed time even on output floods."""
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env, start_new_session=True)
    outputs = {"stdout": bytearray(), "stderr": bytearray()}
    deadline, size = time.monotonic()+timeout, 0
    try:
        process.stdin.write(stdin)
        process.stdin.close()
        with selectors.DefaultSelector() as selector:
            for name in outputs:
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = deadline-time.monotonic()
                require(remaining > 0, "Experiment timed out")
                for key, _ in selector.select(min(remaining, 0.1)):
                    data = os.read(key.fileobj.fileno(), 8192)
                    if not data:
                        selector.unregister(key.fileobj)
                    else:
                        size += len(data)
                        require(size <= limit, "Experiment output limit exceeded")
                        outputs[key.data].extend(data)
        process.wait(timeout=max(0.01, deadline-time.monotonic()))
        require(process.returncode == 0, "Experiment process failed")
        return bytes(outputs["stdout"]), bytes(outputs["stderr"])
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for stream in (process.stdout, process.stderr):
            stream.close()


def analysis_output(output):
    exact(output, ('counts',))
    require(type(output['counts']) is list and 0 < len(output['counts']) <= 32, 'Invalid finite-count evidence')
    ids=set()
    for count in output['counts']:
        exact(count, ('id','tested','satisfied'))
        text(count['id'],128)
        require(count['id'] not in ids, 'Duplicate count ID');ids.add(count['id'])
        integer(count['tested'],1,2**64)
        integer(count['satisfied'],0,count['tested'])
    return output


def run(record, policy, reviewer, private_bytes=None):
    evidence = check_evidence(record)
    require(evidence["experiment_required"], "No experiment requested")
    experiment = evidence["claim"]["experiment"]
    require(experiment["trials"] <= policy["experiment_max_trials"], "Trial limit exceeded")
    verifier, results = Verifier.from_evidence(record), []
    with tempfile.TemporaryDirectory(prefix="curvesmash-experiment-") as temp:
        directory = Path(temp).resolve()
        directory.chmod(0o755)
        for path, file in evidence["files"].items():
            if not path.startswith("candidate/"):
                continue
            dest = directory / path.removeprefix("candidate/")
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
            dest.write_text(file["text"], encoding="utf-8")
            dest.chmod(0o444)
        for trial in range(experiment["trials"]):
            challenge = verifier.challenge() if experiment.get('kind','attack')=='attack' else {
                'track':evidence['track'],'trial':trial,'seed':secrets.token_hex(32)}
            name = "curvesmash-"+uuid.uuid4().hex
            command = docker_command(policy["experiment_image"], directory,
                                     experiment["entrypoint"], name, policy)
            started = time.monotonic()
            try:
                stdout, stderr = bounded_process(command, canonical(challenge)+b"\n",
                    policy["experiment_timeout_seconds"], policy["experiment_output_bytes"])
                output = parse(stdout, policy["experiment_output_bytes"])
                valid = verifier.verify(challenge, output) if experiment.get("kind","attack")=="attack" else None
                if valid is None:analysis_output(output)
                results.append({"challenge": challenge, "output": output, "valid": valid,
                    "elapsed_seconds": time.monotonic()-started, "stderr_sha256": sha(stderr)})
            finally:
                subprocess.run(["docker", "rm", "-f", name],
                               env={"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=10, check=False)
    body = {"kind": "experiment", "reviewer": reviewer,
        "issued_at": datetime.now(timezone.utc).isoformat(), "binding": record["binding"],
        "image": policy["experiment_image"], "results": results,
        "scope": "Finite execution evidence only; attack results are independently checked, analysis counts are program-reported and require scientific review. No production complexity or success bound inferred."}
    if private_bytes is None:
        # The credential-free execution job emits this body. Only the trusted
        # review job may attest its same-run artifact, after rechecking outputs.
        validate_body(body, record, policy)
        return body
    signed = sign(body, private_bytes)
    validate_report(signed, record, policy)
    return signed


def validate_report(report, record, policy):
    body = verify(report, policy, "execution", record["binding"])
    validate_body(body, record, policy)


def validate_body(body, record, policy):
    exact(body, ("kind", "reviewer", "issued_at", "binding", "image", "results", "scope"))
    require(body["kind"] == "experiment" and body["image"] == policy["experiment_image"],
            "Wrong execution provenance")
    docker_command(body["image"], "/unused", "unused.py", "unused", policy)
    expected = record["evidence"]["claim"]["experiment"]["trials"]
    require(type(body["results"]) is list and len(body["results"]) == expected,
            "Incomplete experiment report")
    verifier = Verifier.from_evidence(record)
    for result in body["results"]:
        exact(result, ("challenge", "output", "valid", "elapsed_seconds", "stderr_sha256"))
        if record['evidence']['claim']['experiment'].get('kind','attack')=='attack':
            require(type(result["valid"]) is bool and
                    verifier.verify(result["challenge"], result["output"]) == result["valid"],
                    "Organizer verification disagrees with execution report")
        else:
            exact(result['challenge'],('track','trial','seed'))
            require(result['valid'] is None and result['challenge']['track']==record['evidence']['track'],
                    'Analysis evidence cannot assert a production attack result')
            integer(result['challenge']['trial'],0,expected-1)
            require(type(result['challenge']['seed']) is str and HEX.fullmatch(result['challenge']['seed']), 'Invalid experiment seed')
            analysis_output(result['output'])
        number(result["elapsed_seconds"], 0, policy["experiment_timeout_seconds"]+10)
        require(type(result["stderr_sha256"]) is str and HEX.fullmatch(result["stderr_sha256"]),
                "Invalid log digest")
