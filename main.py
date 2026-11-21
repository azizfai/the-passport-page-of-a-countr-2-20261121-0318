#!/usr/bin/env python3
"""Ship the finished Azmara passport spread to the output directory.

The finished picture lives in this repository as base64 text
(entry.png.b64). This entrypoint uses only the standard library:
it finds the payload, decodes it, checks the PNG magic bytes,
and writes the result to /output/entry.png (or to the directory
MAKEFUN_OUTPUT_DIR names). The grader has no Pillow and no fonts,
so nothing here imports anything beyond the stdlib.
"""

import base64
import hashlib
import os
import sys

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def locate_payload():
    """Find entry.png.b64 next to this file, else in the bot dir."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "entry.png.b64")
    if os.path.isfile(candidate):
        return candidate
    bot_dir = os.environ.get("MAKEFUN_BOT_DIR", "")
    if bot_dir:
        alt = os.path.join(bot_dir, "entry.png.b64")
        if os.path.isfile(alt):
            return alt
    return candidate


def load_image_bytes(path):
    """Decode the base64 payload at path, verifying the PNG header."""
    with open(path, "r", encoding="ascii") as handle:
        text = "".join(handle.read().split())
    try:
        raw = base64.b64decode(text, validate=True)
    except Exception as exc:
        raise ValueError(f"{path} is not valid base64: {exc}") from exc
    if not raw.startswith(PNG_MAGIC):
        raise ValueError(f"{path} does not decode to a PNG image")
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
