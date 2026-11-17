import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import noctalia_app_customize as customize
from src import noctalia_dock_watch as watcher


class DesktopEntryTests(unittest.TestCase):
    def test_filename_normalizes_app_id_once(self):
        self.assertEqual(customize.filename_for("org.telegram.desktop"), "org.telegram.desktop.desktop")
        self.assertEqual(customize.filename_for("org.telegram.desktop.desktop"), "org.telegram.desktop.desktop")

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
        self.assertEqual(watcher.normalize_id("firefox.desktop"), "firefox.desktop")

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            watcher.normalize_id("../../outside")

    def test_finds_desktop_file_in_xdg_data_dir(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = root / "applications"
            apps.mkdir()
            target = apps / "org.example.App.desktop"
            target.write_text("[Desktop Entry]\nName=Example\n", encoding="utf-8")
            with patch.object(watcher, "DATA_HOME", root), patch.dict("os.environ", {"XDG_DATA_DIRS": directory}):
                self.assertEqual(watcher.find_desktop("org.example.App"), target)


if __name__ == "__main__":
    unittest.main()
