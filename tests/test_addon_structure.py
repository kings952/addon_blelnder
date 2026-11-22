import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "app" / "genesis_mocap"


class AddonStructureTests(unittest.TestCase):
    def test_blender_extension_manifest_exists(self):
        manifest = ADDON / "blender_manifest.toml"
        self.assertTrue(manifest.is_file())
        content = manifest.read_text(encoding="utf-8")
        self.assertIn('id = "genesis_mocap"', content)
        self.assertIn('blender_version_min = "5.0.0"', content)

    def test_expected_package_directories_exist(self):
        for relative in ("core", "operators", "ui"):
            self.assertTrue((ADDON / relative / "__init__.py").is_file())

    def test_all_python_files_parse(self):
        python_files = list(ADDON.rglob("*.py"))
        self.assertGreaterEqual(len(python_files), 8)
        for path in python_files:
            with self.subTest(path=path.relative_to(ROOT)):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_tests_are_outside_app_directory(self):
        self.assertTrue((ROOT / "tests").is_dir())
        self.assertFalse((ADDON / "tests").exists())


if __name__ == "__main__":
    unittest.main()
