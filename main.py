#!/usr/bin/env python3
"""Ship the finished Azmara passport spread to the output directory.

The finished picture lives in this repository as entry.png (rendered
locally at build time with Pillow). This entrypoint uses only the
standard library: it finds the PNG, checks the PNG magic bytes and
the expected sha256, and copies it to /output/entry.png (or to the
directory MAKEFUN_OUTPUT_DIR names). The grader has no Pillow and
no fonts, so nothing here imports anything beyond the stdlib.
"""

import hashlib
import os
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
EXPECTED_SHA256 = "c52ef013d17bce603deb00e8d898a09d4fafd222145dda891600a3bf6dd22874"
EXPECTED_BYTES = 387187


def locate_payload():
    """Find entry.png next to this file, else in the bot dir."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "entry.png")
    if os.path.isfile(candidate):
        return candidate
    bot_dir = os.environ.get("MAKEFUN_BOT_DIR", "")
    if bot_dir:
        alt = os.path.join(bot_dir, "entry.png")
        if os.path.isfile(alt):
            return alt
    return candidate


def load_image_bytes(path):
    """Read the PNG payload at path, verifying magic bytes and hash."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if not raw.startswith(PNG_MAGIC):
        raise ValueError(f"{path} does not start with PNG magic bytes")
    if len(raw) != EXPECTED_BYTES:
        raise ValueError(
            f"{path} is {len(raw)} bytes, expected {EXPECTED_BYTES}")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(
            f"{path} sha256 mismatch: got {digest}, "
            f"expected {EXPECTED_SHA256}")
    return raw


def run():
    path = locate_payload()
    if not os.path.isfile(path):
        print(f"error: payload file not found: {path}", file=sys.stderr)
        return 1
    try:
        image = load_image_bytes(path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.png")
        with open(out_path, "wb") as handle:
            handle.write(image)
    except OSError as exc:
        print(f"error: cannot write output: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {out_path}: {len(image)} bytes "
          f"sha256={hashlib.sha256(image).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
