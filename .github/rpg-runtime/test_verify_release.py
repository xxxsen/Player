#!/usr/bin/env python3
"""Regression tests for EasyRPG release marker ownership."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify-release.py")
SPEC = importlib.util.spec_from_file_location("verify_release", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("RPG_RUNTIME_VERIFY_IMPORT_FAILED")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class ReleaseMarkerTests(unittest.TestCase):
    def test_remote_rtp_bridge_marker_belongs_to_wasm(self) -> None:
        self.assertIn(b"runtimeRtpRemoteFiles", VERIFY.WASM_BRIDGE_MARKERS)
        self.assertNotIn("runtimeRtpRemoteFiles", VERIFY.JAVASCRIPT_BRIDGE_MARKERS)

    def test_javascript_pre_run_markers_remain_in_javascript(self) -> None:
        self.assertIn("runtimeRestoreFiles", VERIFY.JAVASCRIPT_BRIDGE_MARKERS)
        self.assertNotIn(b"runtimeRestoreFiles", VERIFY.WASM_BRIDGE_MARKERS)


if __name__ == "__main__":
    unittest.main()
