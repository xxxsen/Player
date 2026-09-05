#!/usr/bin/env python3
"""Regression tests for EasyRPG release marker ownership."""

from __future__ import annotations

import importlib.util
import json
import subprocess
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
    def test_runtime_status_has_no_host_fixture_or_review_protocol(self) -> None:
        source = (ROOT / "src/platform/emscripten/interface.cpp").read_text(encoding="utf-8")
        status = source.split("std::string Emscripten_Interface::RuntimeState() {", 1)[1].split(
            "\n}\n", 1
        )[0]
        for removed in ("fixture_state", "fixtureState", "GetMapId", "GetX", "GetY", "game_variables"):
            self.assertNotIn(removed, status)
        for retained in ("Scene::Map", "Player::IsRPG2k3()", "CanCreateRuntimeCheckpoint()", "Player::GetFrames()"):
            self.assertIn(retained, status)

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

    def test_remote_download_does_not_create_the_current_directory(self) -> None:
        source = (ROOT / "src/async_handler.cpp").read_text(encoding="utf-8")
        guard = source.index('directory == "."')
        create = source.index("FS.mkdirTree(UTF8ToString($0))", guard)
        self.assertLess(guard, create)

    def test_remote_index_materializes_the_declared_directory_tree_before_gameplay(self) -> None:
        source = (ROOT / "src/async_handler.cpp").read_text(encoding="utf-8")
        materialize = source.index("ensure_parent_directories(file_mapping);")
        rtp_mapping = source.index("CreateRuntimeRtpMapping();", materialize)
        self.assertLess(materialize, rtp_mapping)
        self.assertIn("std::unordered_set<std::string> directories;", source)

    def test_emscripten_reports_a_real_player_exit_before_cancelling_the_main_loop(self) -> None:
        source = (ROOT / "src/platform/emscripten/main.cpp").read_text(encoding="utf-8")
        signal = source.index("Module.onRuntimeExitRequested")
        cancel = source.index("emscripten_cancel_main_loop();", signal)
        self.assertLess(signal, cancel)

    def test_candidate_build_returns_container_outputs_to_the_calling_user(self) -> None:
        wrapper = (ROOT / ".github/rpg-runtime/build-candidate.sh").read_text(encoding="utf-8")
        builder = (ROOT / ".github/rpg-runtime/build-easyrpg.sh").read_text(encoding="utf-8")
        self.assertIn('RETROM_HOST_UID="$(id -u)"', wrapper)
        self.assertIn('RETROM_HOST_GID="$(id -g)"', wrapper)
        self.assertIn('--env RETROM_HOST_UID --env RETROM_HOST_GID', wrapper)
        self.assertIn('chown -R -- "$RETROM_HOST_UID:$RETROM_HOST_GID"', builder)

    def test_candidate_build_retries_and_validates_dependency_archives(self) -> None:
        builder = (ROOT / ".github/rpg-runtime/build-easyrpg.sh").read_text(encoding="utf-8")
        patch = (ROOT / ".github/rpg-runtime/easyrpg-download-integrity.patch").read_text(
            encoding="utf-8"
        )

        self.assertIn("easyrpg-download-integrity.patch", builder)
        self.assertIn("verify_download", patch)
        self.assertIn("--retry-all-errors", patch)
        self.assertIn("$file.part", patch)
        self.assertIn("bzip2 -t", patch)
        parsed = subprocess.run(
            ["git", "apply", "--stat", str(ROOT / ".github/rpg-runtime/easyrpg-download-integrity.patch")],
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(0, parsed.returncode, parsed.stderr)


if __name__ == "__main__":
    unittest.main()
