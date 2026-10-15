"""Tooling tests use synthetic fixtures; they do not build or run Card Wars."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("linux_package", ROOT / "scripts/package-linux.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="card wars tests ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.build = self.root / "build with spaces"
        self.build.mkdir()
        self.output = self.root / "dist/game.tar.gz"
        # A header fixture, not a playable binary; only the packager consumes it.
        header = bytearray(64)
        header[:7] = b"\x7fELF\x02\x01\x01"
        struct.pack_into("<HH", header, 16, 2, 62)
        (self.build / "CardWars.x86_64").write_bytes(header)
        for name in (
            "run.sh", "STEAM_DECK.md", "CardWars_Data/Managed/Assembly-CSharp.dll",
            "CardWars_Data/StreamingAssets/server_settings.json",
            "CardWars_Data/StreamingAssets/global_settings.json",
            "CardWars_Data/StreamingAssets/Blueprints/db_Tutorials.json",
            "CardWars_Data/extra data/keep this.bin",
        ):
            target = self.build / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("fixture", encoding="utf-8")
        (self.build / "build-info.json").write_text(json.dumps({
            "target": "StandaloneLinux64", "unityVersion": "2017.4.40f1"
        }), encoding="utf-8")

    def test_package_retains_data_and_sets_permissions_and_checksum(self):
        (self.build / "CardWars.x86_64").chmod(0o644)
        (self.build / "run.sh").chmod(0o644)
        packager.package(self.build, self.output)
        prefix = packager.PACKAGE_NAME + "/"
        with tarfile.open(self.output) as archive:
            for name in ("CardWars.x86_64", "run.sh"):
                self.assertEqual(archive.getmember(prefix + name).mode, 0o755)
            self.assertEqual(archive.extractfile(prefix + "CardWars_Data/extra data/keep this.bin").read(), b"fixture")
            self.assertEqual(archive.getmember(prefix + "CardWars_Data").mode, 0o755)
        checksum = self.output.with_name(self.output.name + ".sha256").read_text()
        self.assertEqual(checksum, hashlib.sha256(self.output.read_bytes()).hexdigest() + "  game.tar.gz\n")
        self.assertEqual((self.build / "run.sh").stat().st_mode & 0o777, 0o644)

    def test_rejects_windows_executable_without_replacing_previous_archive(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b"previous archive")
        (self.build / "CardWars.x86_64").write_bytes(b"MZ" + bytes(62))
        with self.assertRaisesRegex(ValueError, "ELF"):
            packager.package(self.build, self.output)
        self.assertEqual(self.output.read_bytes(), b"previous archive")

    def test_rejects_wrong_architecture(self):
        player = self.build / "CardWars.x86_64"
        header = bytearray(player.read_bytes())
        struct.pack_into("<H", header, 18, 183)  # AArch64, not Steam Deck's x86-64
        player.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "ELF"):
            packager.package(self.build, self.output)

    def test_rejects_missing_game_assembly(self):
        (self.build / "CardWars_Data/Managed/Assembly-CSharp.dll").unlink()
        with self.assertRaisesRegex(ValueError, "Assembly-CSharp"):
            packager.package(self.build, self.output)

    def test_rejects_missing_build_completion_marker(self):
        (self.build / "build-info.json").unlink()
        with self.assertRaisesRegex(ValueError, "build-info"):
            packager.package(self.build, self.output)

    def test_rejects_incorrect_build_metadata(self):
        (self.build / "build-info.json").write_text('{"target":"StandaloneWindows64"}')
        with self.assertRaisesRegex(ValueError, "metadata"):
            packager.package(self.build, self.output)

    def test_rejects_archive_inside_build(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            packager.package(self.build, self.build / "recursive.tar.gz")

    def test_rejects_external_symlink(self):
        (self.root / "outside.txt").write_text("not part of the build")
        (self.build / "external-link").symlink_to(self.root / "outside.txt")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            packager.package(self.build, self.output)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="card wars launcher ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.launcher = self.root / "run.sh"
        shutil.copyfile(ROOT / "scripts/linux/run.sh", self.launcher)
        self.player = self.root / "CardWars.x86_64"

    def launch(self, *args):
        return subprocess.run(["bash", str(self.launcher)] + list(args), cwd="/",
                              text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=dict(os.environ, CARDWARS_TEST_SENTINEL="preserved"))

    def test_reports_missing_data(self):
        self.assertIn("missing", self.launch().stderr)
        self.assertNotEqual(self.launch().returncode, 0)

    def test_reports_non_executable_player(self):
        (self.root / "CardWars_Data").mkdir()
        self.player.write_text("fixture")
        self.player.chmod(0o644)
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not executable", result.stderr)

    def test_preserves_arguments_environment_working_directory_and_exit_status(self):
        (self.root / "CardWars_Data").mkdir()
        # An explicit launcher probe, not a Unity player or a shipping artifact.
        self.player.write_text('#!/usr/bin/env python3\nimport os,sys,json\n'
                              'print(json.dumps([os.getcwd(),sys.argv[1:],os.environ["CARDWARS_TEST_SENTINEL"]]))\n'
                              'sys.exit(37)\n')
        self.player.chmod(0o755)
        arguments = ["-screen-fullscreen", "0", "-logFile", "log with spaces.txt", "$(literal)"]
        result = self.launch(*arguments)
        self.assertEqual(result.returncode, 37)
        self.assertEqual(json.loads(result.stdout), [str(self.root), arguments, "preserved"])


if __name__ == "__main__":
    unittest.main()
