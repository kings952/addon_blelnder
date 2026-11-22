"""Launch Blender in background and inspect .blend files without enabling the add-on."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class BlendInspectionError(RuntimeError):
    """A readable error raised when the .blend inspection cannot finish."""


class BlendInspector:
    def __init__(self, blender_executable: Optional[str] = None, timeout: int = 180):
        self.blender_executable = blender_executable
        self.timeout = timeout

    def resolve_executable(self) -> str:
        candidate = self.blender_executable or os.environ.get("BLENDER_EXECUTABLE")
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
        if candidate:
            found = shutil.which(candidate)
            if found:
                return found
            raise BlendInspectionError("No se encontró Blender: {}".format(candidate))
        found = shutil.which("blender") or shutil.which("blender.exe")
        if found:
            return found
        raise BlendInspectionError(
            "No se encontró Blender. Indica blender.exe en la ventana o define BLENDER_EXECUTABLE."
        )

    def inspect(self, blend_path: str) -> Dict[str, Any]:
        source = Path(blend_path).expanduser().resolve()
        if not source.is_file():
            raise BlendInspectionError("El archivo .blend no existe: {}".format(source))
        if source.suffix.lower() != ".blend":
            raise BlendInspectionError("Selecciona un archivo con extensión .blend.")

        executable = self.resolve_executable()
        worker = Path(__file__).with_name("blender_worker.py")
        if not worker.is_file():
            raise BlendInspectionError("No se encontró el script inspector: {}".format(worker))

        with tempfile.TemporaryDirectory(prefix="genesis_blend_check_") as temp_dir:
            output = Path(temp_dir) / "inspection.json"
            command = [
                executable, "--background", "--factory-startup", str(source),
                "--python", str(worker), "--python-exit-code", "1",
                "--", "--output", str(output),
            ]
            try:
                process = subprocess.run(
                    command, capture_output=True, text=True, encoding="utf-8",
                    errors="replace", timeout=self.timeout, check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise BlendInspectionError(
                    "Blender superó el tiempo límite de {} segundos.".format(self.timeout)
                ) from exc
            except OSError as exc:
                raise BlendInspectionError("No se pudo iniciar Blender: {}".format(exc)) from exc

            if process.returncode != 0:
                detail = (process.stderr or process.stdout or "Sin detalles de Blender").strip()
                raise BlendInspectionError(
                    "Blender no pudo leer el archivo (código {}).\n{}".format(process.returncode, detail[-5000:])
                )
            if not output.is_file():
                detail = (process.stderr or process.stdout or "").strip()
                raise BlendInspectionError("Blender no generó el informe. {}".format(detail[-3000:]))
            try:
                data = json.loads(output.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise BlendInspectionError("El informe de Blender no es JSON válido.") from exc

        if not isinstance(data, dict) or not isinstance(data.get("armatures"), list):
            raise BlendInspectionError("El informe no contiene una lista válida de armatures.")
        return data

    @staticmethod
    def validate_armature(inspection: Dict[str, Any], armature_name: str) -> Dict[str, Any]:
        armatures: List[Dict[str, Any]] = inspection.get("armatures", [])
        selected = next((item for item in armatures if item.get("name") == armature_name), None)
        if selected is None:
            raise BlendInspectionError("No existe el armature seleccionado en el informe.")

        import sys
        app_dir = str(Path(__file__).resolve().parents[1])
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        from genesis_mocap.core.armature_validator import validate_genesis_bones

        report = validate_genesis_bones(selected.get("bones", []))
        return {
            "armature_name": armature_name,
            "bone_count": selected.get("bone_count", len(selected.get("bones", []))),
            "is_valid": report.is_valid,
            "total_targets": report.total_targets,
            "required_bones": report.required_bones,
            "found_count": report.found_count,
            "missing_count": report.missing_count,
            "percentage": round(report.percentage, 2),
            "found_bones": list(report.found_bones),
            "missing_bones": list(report.missing_bones),
            "auxiliary_targets": list(report.auxiliary_targets),
        }
