import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTER = ROOT / "app" / "genesis_mocap_tester"


class VisionTesterStructureTests(unittest.TestCase):
    def test_single_tester_has_both_phase_tabs(self):
        gui = (TESTER / "gui.py").read_text(encoding="utf-8")
        self.assertIn("Fase 1 · Inspector de rigs", gui)
        self.assertIn("Fase 2 · Motor de visión", gui)
        self.assertIn("VisionCapturePanel", gui)

    def test_capture_image_video_and_camera_controls_exist(self):
        source = (TESTER / "vision_panel.py").read_text(encoding="utf-8")
        for item in ("open_image", "detect_image", "open_video", "open_camera", "VideoCapture"):
            self.assertIn(item, source)

    def test_subject_selection_and_skeleton_rendering_exist(self):
        source = (TESTER / "vision_panel.py").read_text(encoding="utf-8")
        for item in ("_select_subject", "_select_from_list", "_draw_detections", "POSE_CONNECTIONS", "Puntos visibles"):
            self.assertIn(item, source)

    def test_detector_supports_image_and_video_modes(self):
        source = (TESTER / "vision.py").read_text(encoding="utf-8")
        self.assertIn("RunningMode.VIDEO", source)
        self.assertIn("RunningMode.IMAGE", source)
        self.assertIn("def detect_image", source)
        self.assertIn("num_poses=self.max_people", source)

    def test_tester_python_files_parse(self):
        for path in TESTER.glob("*.py"):
            with self.subTest(file=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
