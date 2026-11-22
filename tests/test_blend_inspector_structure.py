import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTER = ROOT / "app" / "genesis_mocap_tester"


class BlendInspectorStructureTests(unittest.TestCase):
    def test_standalone_tester_entrypoint_exists(self):
        for name in ("__main__.py", "gui.py", "runner.py", "blender_worker.py"):
            self.assertTrue((TESTER / name).is_file())

    def test_worker_reads_armatures_without_saving_the_source_file(self):
        source = (TESTER / "blender_worker.py").read_text(encoding="utf-8")
        self.assertIn("bpy.data.objects", source)
        self.assertIn('obj.type != "ARMATURE"', source)
        self.assertIn('"bone_details"', source)
        self.assertNotIn("bpy.ops.wm.save_as_mainfile", source)
        self.assertNotIn("bpy.ops.wm.save_mainfile", source)

    def test_gui_has_file_picker_and_armature_selector(self):
        source = (TESTER / "gui.py").read_text(encoding="utf-8")
        self.assertIn("askopenfilename", source)
        self.assertIn("Combobox", source)
        self.assertIn("Validar seleccionado", source)

    def test_all_tester_sources_parse(self):
        for path in TESTER.glob("*.py"):
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


if __name__ == "__main__":
    unittest.main()
