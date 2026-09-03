#!/usr/bin/env python3
"""Regression tests for EasyRPG release marker ownership."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify-release.py")
ROOT = SCRIPT.parents[2]
SPEC = importlib.util.spec_from_file_location("verify_release", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("RPG_RUNTIME_VERIFY_IMPORT_FAILED")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReleaseMarkerTests(unittest.TestCase):
    def test_release_identity_uses_the_organization_and_core_tag_namespace(self) -> None:
        contract = json.loads((ROOT / "retrom-fork.json").read_text(encoding="utf-8"))
        workflow = (ROOT / ".github/workflows/rpg-runtime-release.yml").read_text(encoding="utf-8")

        self.assertEqual(contract["forkRepository"], "https://github.com/retrom-project/Player")
        self.assertTrue(VERIFY.TAG.fullmatch("retrom-core-0.8.1.1-r6"))
        self.assertIsNone(VERIFY.TAG.fullmatch("rpg-runtime-0.8.1.1-r6"))
        self.assertIn('"retrom-core-0.8.1.1-r*"', workflow)

    def test_remote_rtp_bridge_marker_belongs_to_wasm(self) -> None:
        self.assertIn(b"runtimeRtpRemoteFiles", VERIFY.WASM_BRIDGE_MARKERS)
        self.assertNotIn("runtimeRtpRemoteFiles", VERIFY.JAVASCRIPT_BRIDGE_MARKERS)

    def test_javascript_pre_run_markers_remain_in_javascript(self) -> None:
        self.assertIn("runtimeRestoreFiles", VERIFY.JAVASCRIPT_BRIDGE_MARKERS)
        self.assertNotIn(b"runtimeRestoreFiles", VERIFY.WASM_BRIDGE_MARKERS)

    def test_remote_download_creates_the_destination_parent_before_wget(self) -> None:
        source = (ROOT / "src/async_handler.cpp").read_text(encoding="utf-8")
        self.assertIn("FS.mkdirTree(UTF8ToString($0))", source)
        ensure = source.index("ensure_parent_directory(file);")
        download = source.index("start_async_wget_with_retry(ctx);", ensure)
        self.assertLess(ensure, download)

    def test_candidate_build_returns_container_outputs_to_the_calling_user(self) -> None:
        wrapper = (ROOT / ".github/rpg-runtime/build-candidate.sh").read_text(encoding="utf-8")
        builder = (ROOT / ".github/rpg-runtime/build-easyrpg.sh").read_text(encoding="utf-8")
        self.assertIn('RETROM_HOST_UID="$(id -u)"', wrapper)
        self.assertIn('RETROM_HOST_GID="$(id -g)"', wrapper)
        self.assertIn('--env RETROM_HOST_UID --env RETROM_HOST_GID', wrapper)
        self.assertIn('chown -R -- "$RETROM_HOST_UID:$RETROM_HOST_GID"', builder)


if __name__ == "__main__":
    unittest.main()
