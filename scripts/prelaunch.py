#!/usr/bin/env python3
"""Check a prelaunch scaffold without executing or scoring candidate content."""
import argparse
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular organizer file: {path.name}")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=nonfinite)


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Invalid repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise ValueError("Noncanonical repository-relative path")
    return path


def validate(root=ROOT):
    manifest = read_json(root / "benchmark.json")
    profiles = read_json(root / "target-profiles/production-draft.json")
    cost = read_json(root / "cost-models/production-draft.json")
    if manifest.get("schemaVersion") != 2 or manifest.get("name") != "curvesmash":
        raise ValueError("Wrong manifest identity or schema")
    if profiles.get("state") != "draft" or cost.get("state") != "draft":
        raise ValueError("This scaffold cannot assert scientific qualification")
    if cost.get("metric") != "time_log2" or cost.get("direction") != "-":
        raise ValueError("Changed headline metric")
    if cost.get("success_probability_minimum") != 0.9:
        raise ValueError("Changed draft success contract")
    targets = profiles["targets"]
    if len(targets) != 6 or len({t["id"] for t in targets}) != 6:
        raise ValueError("Expected six unique production targets")
    names = {t["id"] + "-exploratory" for t in targets}
    tracks = manifest["tracks"]
    if len(tracks) != 6 or {t["name"] for t in tracks} != names:
        raise ValueError("Manifest and protected target registry differ")
    for target in targets:
        if target.get("scope") != "unrestricted-production":
            raise ValueError("Supporting experiments cannot become headline targets")
        if target.get("qualified_baseline") is not None:
            raise ValueError("Baseline qualification is not implemented")
    editable = []
    for track in tracks:
        name = track["name"]
        target_id = name.removesuffix("-exploratory")
        expected = f"candidates/{target_id}"
        if track.get("editablePaths") != [expected]:
            raise ValueError("Candidate paths must be exact and disjoint")
        path = relative_path(expected)
        candidate = root / path
        if candidate.is_symlink() or not candidate.is_dir():
            raise ValueError("Candidate root must be a direct directory")
        editable.append(path)
        if track.get("promotionMode") != "manual" or track.get("direction") != "-":
            raise ValueError("Manual promotion and lower cost are required")
        expected_score = f".yukon/scores/{name}.json"
        if track.get("scorePath") != expected_score:
            raise ValueError("Wrong independent score path")
        relative_path(expected_score)
        if (root / expected_score).exists() or (root / expected_score).is_symlink():
            raise ValueError("A prelaunch scaffold cannot contain leaderboard scores")
        if track.get("benchmarkCommand") != ["python3", "scripts/prelaunch.py",
                                                "--track", name, "--require-ready"]:
            raise ValueError("Production evaluation is not implemented")
    for i, path in enumerate(editable):
        for other in editable[i + 1:]:
            if path == other or path in other.parents or other in path.parents:
                raise ValueError("Editable paths overlap")
    return manifest, profiles, cost


def readiness_errors(profiles, cost):
    # No status field or participant claim can enable scoring in this scaffold.
    errors = ["Independent verifiers, isolated execution, authenticated review and scoring are not implemented.",
              "Live Yukon registration, baseline jobs and manual promotion have not been verified.",
              "Scientific review committee and held-out calibration are not established."]
    errors.extend(cost["unresolved"])
    for target in profiles["targets"]:
        errors.extend(f"{target['id']}: {item}" for item in target["unresolved"])
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--track")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        manifest, profiles, cost = validate()
        if args.track and args.track not in {t["name"] for t in manifest["tracks"]}:
            raise ValueError("Unknown track")
        if args.require_ready:
            print("PRELAUNCH: no score emitted.")
            for error in readiness_errors(profiles, cost):
                print(f"- {error}")
            return 2
        print("Local scaffold consistent: six unrestricted production tracks; no scores; launch readiness pending.")
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Prelaunch check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
