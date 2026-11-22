import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

from genesis_mocap.core.bone_mapping import (
    AUXILIARY_TARGET_BONES,
    EXPECTED_TARGET_BONES,
    GENESIS_BONE_MAP,
    REQUIRED_GENESIS_BONES,
)


class BoneMappingTests(unittest.TestCase):
    def test_mapping_contains_exactly_58_ordered_targets(self):
        self.assertEqual(len(GENESIS_BONE_MAP), 58)
        self.assertEqual([item.index for item in GENESIS_BONE_MAP], list(range(1, 59)))
        self.assertEqual(len({item.target_name for item in GENESIS_BONE_MAP}), 58)

    def test_required_and_auxiliary_counts_match_specification(self):
        self.assertEqual(EXPECTED_TARGET_BONES, 58)
        self.assertEqual(len(REQUIRED_GENESIS_BONES), 52)
        self.assertEqual(len(AUXILIARY_TARGET_BONES), 6)

    def test_genesis_source_names_are_unique(self):
        self.assertEqual(len(REQUIRED_GENESIS_BONES), len(set(REQUIRED_GENESIS_BONES)))

    def test_special_genesis_names_are_present(self):
        self.assertIn("rShldrBend", REQUIRED_GENESIS_BONES)
        self.assertIn("rShldrTwist", REQUIRED_GENESIS_BONES)
        self.assertIn("lShldrBend", REQUIRED_GENESIS_BONES)
        self.assertIn("lShldrTwist", REQUIRED_GENESIS_BONES)
        self.assertIn("rPinky1", REQUIRED_GENESIS_BONES)
        self.assertIn("lThumb3", REQUIRED_GENESIS_BONES)


if __name__ == "__main__":
    unittest.main()
