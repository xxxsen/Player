#!/usr/bin/env python3
"""Validate the Retrom EasyRPG release pair and emit non-authoritative metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


TAG = re.compile(r"^retrom-web-0\.8\.1\.1-r[1-9][0-9]*$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    if TAG.fullmatch(args.tag) is None or COMMIT.fullmatch(args.commit) is None:
        raise SystemExit("RETROM_RELEASE_IDENTITY_INVALID")

    js_path = args.output / "easyrpg-player.js"
    wasm_path = args.output / "easyrpg-player.wasm"
    if js_path.is_symlink() or not js_path.is_file() or js_path.stat().st_size < 200_000:
        raise SystemExit("RETROM_RELEASE_JS_INVALID")
    if wasm_path.is_symlink() or not wasm_path.is_file() or wasm_path.stat().st_size < 8_000_000:
        raise SystemExit("RETROM_RELEASE_WASM_INVALID")
    wasm = wasm_path.read_bytes()
    if wasm[:8] != b"\x00asm\x01\x00\x00\x00":
        raise SystemExit("RETROM_RELEASE_WASM_INVALID")
    if b"/runtime/rpg-project/" not in wasm:
        raise SystemExit("RETROM_RELEASE_GAME_URL_INVALID")

    javascript = js_path.read_text(encoding="utf-8")
    required_markers = (
        "retrom-filesystem-ready",
        "retromRestoreFiles",
        "retromRestoreSlot",
        "retromRtpFiles",
        "retromEngineMode",
    )
    if any(marker not in javascript for marker in required_markers):
        raise SystemExit("RETROM_RELEASE_BRIDGE_INVALID")

    assets = []
    for path in (js_path, wasm_path):
        assets.append(
            {
                "filename": path.name,
                "observedSha256": digest(path),
                "sizeBytes": path.stat().st_size,
            }
        )
    metadata = {
        "adapterAbi": "easyrpg-save-v1",
        "assets": assets,
        "commit": args.commit,
        "digestPolicy": "OBSERVED_CACHE_INTEGRITY_ONLY",
        "repository": args.repository,
        "schemaVersion": 1,
        "tag": args.tag,
    }
    (args.output / "retrom-runtime-release.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
