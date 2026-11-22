import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from genesis_mocap.core.armature_validator import (
    validate_genesis_bones,
    validate_armature_object,
)
from genesis_mocap.core.bone_mapping import REQUIRED_GENESIS_BONES


class FakeBone:
    def __init__(self, name):
        self.name = name


class FakeArmatureData:
    def __init__(self, names):
        self.bones = [FakeBone(name) for name in names]


class FakeObject:
    type = "ARMATURE"

    def __init__(self, names):
        self.data = FakeArmatureData(names)


class ArmatureValidatorTests(unittest.TestCase):
    def test_complete_genesis_profile_is_valid(self):
        report = validate_genesis_bones(REQUIRED_GENESIS_BONES)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.found_count, 52)
        self.assertEqual(report.missing_count, 0)
        self.assertEqual(report.total_targets, 58)
        self.assertEqual(report.percentage, 100.0)

    def test_missing_bones_are_reported_by_exact_name(self):
        available = [name for name in REQUIRED_GENESIS_BONES if name != "pelvis"]
        report = validate_genesis_bones(available)
        self.assertFalse(report.is_valid)
        self.assertEqual(report.missing_bones, ("pelvis",))
        self.assertEqual(report.found_count, 51)

    def test_empty_armature_reports_all_required_bones_missing(self):
        report = validate_genesis_bones([])
        self.assertFalse(report.is_valid)
        self.assertEqual(report.missing_count, 52)
        self.assertEqual(report.found_count, 0)
        self.assertEqual(report.percentage, 0.0)

    def test_extra_bones_do_not_invalidate_armature(self):
        report = validate_genesis_bones(list(REQUIRED_GENESIS_BONES) + ["ExtraBone"])
        self.assertTrue(report.is_valid)
        self.assertEqual(report.found_count, 52)

    def test_blender_object_adapter_accepts_armature(self):
        report = validate_armature_object(FakeObject(REQUIRED_GENESIS_BONES))
        self.assertTrue(report.is_valid)

    def test_blender_object_adapter_rejects_non_armature(self):
        with self.assertRaises(ValueError):
            validate_armature_object(type("Mesh", (), {"type": "MESH"})())

    def test_none_object_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_armature_object(None)


if __name__ == "__main__":
    unittest.main()
