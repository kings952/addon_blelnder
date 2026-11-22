import ast, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TESTER = ROOT / "app" / "genesis_mocap_tester"

class VisionTesterStructureTests(unittest.TestCase):
    def test_single_tester_has_both_phase_tabs(self):
        gui = (TESTER / "gui.py").read_text(encoding="utf-8")
        self.assertIn("Fase 1 · Inspector de rigs", gui)
        self.assertIn("Fase 2 · Motor de visión", gui)
        self.assertIn("VisionCapturePanel", gui)

    def test_capture_and_selection_controls_exist(self):
        source = (TESTER / "vision_panel.py").read_text(encoding="utf-8")
        for item in ("VideoCapture", "open_camera", "open_video", "_select_subject", "OBJETIVO"):
            self.assertIn(item, source)

    def test_detector_supports_multiple_poses(self):
        source = (TESTER / "vision.py").read_text(encoding="utf-8")
        self.assertIn("num_poses=max(1, int(max_people))", source)
        self.assertIn("PoseLandmarker", source)
        self.assertIn("PersonTracker", source)

    def test_tester_python_files_parse(self):
        for path in TESTER.glob("*.py"):
            with self.subTest(file=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

if __name__ == "__main__": unittest.main()
