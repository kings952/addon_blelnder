import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from genesis_mocap_tester.vision import POSE_CONNECTIONS, PersonTracker, default_model_path


class PersonTrackerTests(unittest.TestCase):
    def test_multiple_people_receive_distinct_ids(self):
        result = PersonTracker().update([
            {"bbox": (0, 0, 20, 40), "center": (0.1, 0.2)},
            {"bbox": (100, 0, 120, 40), "center": (0.8, 0.2)},
        ])
        self.assertEqual(len({p["track_id"] for p in result}), 2)

    def test_small_movement_keeps_track_id(self):
        tracker = PersonTracker()
        first = tracker.update([{"bbox": (0, 0, 20, 40), "center": (0.10, 0.20)}])[0]["track_id"]
        second = tracker.update([{"bbox": (2, 1, 22, 41), "center": (0.11, 0.21)}])[0]["track_id"]
        self.assertEqual(first, second)

    def test_far_detection_gets_new_id(self):
        tracker = PersonTracker(max_distance=0.1)
        first = tracker.update([{"bbox": (0, 0, 20, 20), "center": (0.02, 0.02)}])[0]["track_id"]
        second = tracker.update([{"bbox": (800, 800, 900, 900), "center": (0.9, 0.9)}])[0]["track_id"]
        self.assertNotEqual(first, second)

    def test_default_model_filename(self):
        self.assertEqual(default_model_path().name, "pose_landmarker_lite.task")

    def test_pose_skeleton_has_connections(self):
        self.assertGreaterEqual(len(POSE_CONNECTIONS), 30)
        self.assertIn((11, 13), POSE_CONNECTIONS)
        self.assertIn((23, 25), POSE_CONNECTIONS)


if __name__ == "__main__":
    unittest.main()
