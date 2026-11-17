import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import noctalia_app_customize as customize
from src import noctalia_dock_watch as watcher


class DesktopEntryTests(unittest.TestCase):
    def test_locale_selects_russian_or_english(self):
        with patch.dict(os.environ, {"LC_ALL": "ru_RU.UTF-8"}, clear=True):
            self.assertTrue(customize.is_russian())
            self.assertEqual(customize.tr("Rename", "Переименовать"), "Переименовать")
        with patch.dict(os.environ, {"LC_ALL": "en_US.UTF-8"}, clear=True):
            self.assertFalse(customize.is_russian())
            self.assertEqual(customize.tr("Rename", "Переименовать"), "Rename")

    def test_language_falls_back_to_lang(self):
        with patch.dict(os.environ, {"LANG": "ru_RU.UTF-8"}, clear=True):
            self.assertTrue(customize.is_russian())

    def test_filename_preserves_normalized_desktop_filename(self):
        self.assertEqual(customize.filename_for("org.telegram.desktop.desktop"), "org.telegram.desktop.desktop")
        self.assertEqual(customize.filename_for("firefox.desktop"), "firefox.desktop")

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            customize.filename_for("../outside")

    def test_reads_only_main_desktop_entry(self):
        lines = [
            "[Desktop Entry]", "Name=Original", "Icon=app-icon",
            "[Desktop Action Open]", "Name=Open",
        ]
        self.assertEqual(customize.read_main(lines), {"Name": "Original", "Icon": "app-icon"})

    def test_edit_main_preserves_other_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.desktop"
            path.write_text("[Desktop Entry]\nName=Old\nIcon=old\n[Desktop Action Open]\nName=Open\n", encoding="utf-8")
            customize.edit_main(path, name="New name", icon="/tmp/new.png")
            result = path.read_text(encoding="utf-8")
            self.assertIn("Name=New name", result)
            self.assertIn("Name[ru]=New name", result)
            self.assertIn("Icon=/tmp/new.png", result)
            self.assertIn("[Desktop Action Open]", result)

    def test_add_and_remove_custom_actions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample.desktop"
            path.write_text("[Desktop Entry]\nName=Sample\nActions=Existing;\n\n[Desktop Action Existing]\nName=Existing\n", encoding="utf-8")
            with patch.object(customize, "APPS", root):
                customize.add_actions("sample.desktop")
                added = path.read_text(encoding="utf-8")
                self.assertIn("NoctaliaChangeIcon", added)
                self.assertIn("NoctaliaRename", added)
                self.assertIn("NoctaliaReset", added)
                customize.remove_actions(path)
                cleaned = path.read_text(encoding="utf-8")
                self.assertNotIn("NoctaliaChangeIcon", cleaned)
                self.assertIn("[Desktop Action Existing]", cleaned)


class WatcherTests(unittest.TestCase):
    def test_normalizes_application_ids(self):
        self.assertEqual(watcher.normalize_id("org.telegram.desktop"), "org.telegram.desktop.desktop")
        self.assertEqual(watcher.normalize_id("firefox.desktop"), "firefox.desktop.desktop")

    def test_rejects_path_traversal(self):
        for value in ("../../outside", "../bad.desktop", "bad\\name", "bad\x00name"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                watcher.normalize_id(value)

    def test_finds_desktop_file_in_xdg_data_dir(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = root / "applications"
            apps.mkdir()
            target = apps / "org.example.App.desktop"
            target.write_text("[Desktop Entry]\nName=Example\n", encoding="utf-8")
            with patch.object(watcher, "DATA_HOME", root), patch.dict("os.environ", {"XDG_DATA_DIRS": directory}):
                self.assertEqual(watcher.find_desktop("org.example.App.desktop"), target)

    def test_manifest_rejects_paths_and_non_list_data(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps(["safe.desktop", "../outside.desktop", "/tmp/x.desktop", "bad\\x.desktop", 7]), encoding="utf-8")
            with patch.object(watcher, "MANIFEST", manifest):
                self.assertEqual(watcher.load_manifest(), {"safe.desktop"})
            manifest.write_text(json.dumps({"safe.desktop": True}), encoding="utf-8")
            with patch.object(watcher, "MANIFEST", manifest), patch.object(watcher, "LOG", Path(directory) / "missing.log"):
                self.assertEqual(watcher.load_manifest(), set())

    def test_atomic_json_replaces_state_and_uses_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            watcher.atomic_json(path, ["one.desktop"])
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), ["one.desktop"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(directory).glob(".state.json.*")), [])

    def test_replaced_launcher_is_not_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = root / "applications"
            apps.mkdir()
            target = apps / "sample.desktop"
            target.write_text("[Desktop Entry]\nName=My replacement\nExec=custom-command\n", encoding="utf-8")
            managed = {"sample.desktop"}
            with patch.object(watcher, "LOCAL_APPS", apps), patch.object(watcher, "MANIFEST", root / "manifest.json"), patch.object(watcher, "STATE", root / "state"), patch.object(watcher, "ICONS", root / "icons"):
                watcher.remove_managed_file("sample.desktop", managed)
            self.assertTrue(target.exists())
            self.assertIn("sample.desktop", managed)

    def test_symlink_launcher_is_not_deleted_or_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = root / "applications"
            apps.mkdir()
            outside = root / "outside.desktop"
            outside.write_text("[Desktop Entry]\nName=Keep\n", encoding="utf-8")
            target = apps / "sample.desktop"
            target.symlink_to(outside)
            managed = {"sample.desktop"}
            with patch.object(watcher, "LOCAL_APPS", apps), patch.object(watcher, "MANIFEST", root / "manifest.json"), patch.object(watcher, "STATE", root / "state"), patch.object(watcher, "ICONS", root / "icons"):
                watcher.remove_managed_file("sample.desktop", managed)
            self.assertTrue(target.is_symlink())
            self.assertTrue(outside.exists())

    def test_action_cleanup_skips_unrecognized_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.desktop"
            target.write_text("[Desktop Entry]\nName=Replacement\n", encoding="utf-8")
            with patch.object(watcher, "LOCAL_APPS", root), patch("src.noctalia_dock_watch.subprocess.run") as run:
                self.assertFalse(watcher.remove_actions_for("sample.desktop"))
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
