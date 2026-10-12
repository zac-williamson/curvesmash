"""Bounded input, canonical records, and safe output primitives."""
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

MAX_BYTES = 4 * 1024 * 1024
ARTIFACT_BYTES = 32 * 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9_.-]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value, keys):
    require(type(value) is dict and set(value) == set(keys),
            "Object has missing or unexpected fields")


def text(value, limit=65536):
    require(type(value) is str and 0 < len(value) <= limit and "\x00" not in value,
            "Expected bounded nonempty text")
    return value


def number(value, minimum=0, maximum=4096):
    require(type(value) in (int, float) and minimum <= value <= maximum
            and (type(value) is int or math.isfinite(value)), "Invalid numeric bound")
    return value


def integer(value, minimum=0, maximum=1 << 512):
    require(type(value) is int and minimum <= value <= maximum, "Invalid integer")
    return value


def decimal_integer(value, minimum=0):
    require(type(value) is str and re.fullmatch(r"0|[1-9][0-9]{0,511}", value),
            "Expected a canonical bounded decimal integer string")
    result = int(value)
    require(result >= minimum, "Integer below minimum")
    return result


def relative(value):
    text(value, 256)
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value and
            all(NAME.fullmatch(x) and x not in (".", "..") for x in p.parts),
            "Invalid relative path")
    return p


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse(data, limit=MAX_BYTES):
    if type(data) is str:
        data = data.encode("utf-8")
    require(len(data) <= limit, "JSON exceeds byte limit")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def bad_constant(value):
        raise ValueError("Nonfinite JSON number")

    result = json.loads(data, object_pairs_hook=unique, parse_constant=bad_constant)

    def bounded(value, depth=0):
        require(depth <= 32, "JSON nesting limit exceeded")
        if isinstance(value, (dict, list)):
            require(len(value) <= 1024, "JSON collection limit exceeded")
            for child in (value.values() if isinstance(value, dict) else value):
                bounded(child, depth+1)
        if type(value) is float:
            require(math.isfinite(value), "Nonfinite JSON number")
    bounded(result)
    return result


def read_file(path, limit=MAX_BYTES):
    """Refuse links in every component, special files, and concurrent file mutation."""
    path = Path(path).absolute()
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                    "Expected a regular file without hard links")
            require(before.st_size <= limit, "File exceeds byte limit")
            with os.fdopen(os.dup(file_fd), "rb") as stream:
                data = stream.read(limit+1)
            after = os.fstat(file_fd)
            require(len(data) <= limit and (before.st_ino, before.st_size, before.st_mtime_ns,
                    before.st_ctime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns,
                    after.st_ctime_ns), "File changed while reading")
            return data
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def read_json(path, limit=MAX_BYTES):
    return parse(read_file(path, limit), limit)


def write_new(path, value):
    """Never overwrite or follow a pre-existing artifact, including a stale score."""
    path = Path(path).absolute()
    # Output directories belong to the organizer; reject redirected directories.
    for parent in reversed(path.parents):
        require(not parent.is_symlink(), "Symlinked output directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical(value) + b"\n"
    require(len(data) <= ARTIFACT_BYTES, "Artifact exceeds byte limit")
    fd, temporary = tempfile.mkstemp(prefix="."+path.name+"-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Link publishes the complete file atomically and cannot replace any existing target.
        os.link(temporary, path, follow_symlinks=False)
    finally:
        Path(temporary).unlink(missing_ok=True)
