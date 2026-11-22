import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from genesis_mocap.core.bone_mapping import REQUIRED_GENESIS_BONES
from genesis_mocap_tester.runner import BlendInspectionError, BlendInspector


class BlendInspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.blend = self.root / "sample.blend"
        self.blend.write_bytes(b"placeholder; Blender process is mocked")
        self.executable = self.root / "blender.exe"
        self.executable.write_bytes(b"mock executable")

    def tearDown(self):
        self.temp.cleanup()

    def fake_run(self, armatures, returncode=0):
        def run(command, **kwargs):
            output = Path(command[command.index("--output") + 1])
            output.write_text(json.dumps({
                "blend_file": str(self.blend), "blender_version": "5.3.0",
                "object_count": len(armatures), "armature_count": len(armatures),
                "armatures": armatures,
            }), encoding="utf-8")
            return type("Process", (), {"returncode": returncode, "stdout": "", "stderr": ""})()
        return run

    def test_background_command_returns_all_armatures(self):
        rigs = [{"name": "Genesis", "data_name": "GenesisRig", "bone_count": 52,
                 "bones": list(REQUIRED_GENESIS_BONES), "bone_details": []}]
        with patch("genesis_mocap_tester.runner.subprocess.run", side_effect=self.fake_run(rigs)) as run:
            result = BlendInspector(str(self.executable)).inspect(str(self.blend))
        self.assertEqual(result["armatures"][0]["name"], "Genesis")
        args = run.call_args.args[0]
        for flag in ("--background", "--factory-startup", "--python-exit-code"):
            self.assertIn(flag, args)

    def test_selected_armature_is_validated(self):
        rigs = [
            {"name": "Complete", "bone_count": 52, "bones": list(REQUIRED_GENESIS_BONES)},
            {"name": "Partial", "bone_count": 1, "bones": ["pelvis"]},
        ]
        report = BlendInspector.validate_armature({"armatures": rigs}, "Partial")
        self.assertFalse(report["is_valid"])
        self.assertEqual(report["found_count"], 1)
        self.assertEqual(report["missing_count"], 51)

    def test_unknown_armature_is_rejected(self):
        with self.assertRaises(BlendInspectionError):
            BlendInspector.validate_armature({"armatures": []}, "Missing")

    def test_wrong_extension_is_rejected_before_blender(self):
        other = self.root / "not_blend.txt"
        other.write_text("x", encoding="utf-8")
        with patch("genesis_mocap_tester.runner.subprocess.run") as run:
            with self.assertRaises(BlendInspectionError):
                BlendInspector(str(self.executable)).inspect(str(other))
        run.assert_not_called()

    def test_missing_file_is_rejected(self):
        with self.assertRaises(BlendInspectionError):
            BlendInspector(str(self.executable)).inspect(str(self.root / "missing.blend"))

    def test_blender_nonzero_exit_is_reported(self):
        with patch("genesis_mocap_tester.runner.subprocess.run", side_effect=self.fake_run([], 2)):
            with self.assertRaises(BlendInspectionError):
                BlendInspector(str(self.executable)).inspect(str(self.blend))

    def test_timeout_is_reported(self):
        import subprocess
        with patch("genesis_mocap_tester.runner.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("blender", 1)):
            with self.assertRaisesRegex(BlendInspectionError, "tiempo límite"):
                BlendInspector(str(self.executable), timeout=1).inspect(str(self.blend))

    def test_file_without_armatures_is_supported(self):
        with patch("genesis_mocap_tester.runner.subprocess.run", side_effect=self.fake_run([])):
            result = BlendInspector(str(self.executable)).inspect(str(self.blend))
        self.assertEqual(result["armatures"], [])


if __name__ == "__main__":
    unittest.main()
