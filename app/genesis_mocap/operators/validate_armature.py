"""Blender operator to validate the selected Genesis armature."""

import bpy

from ..core.armature_validator import validate_armature_object


class GENESIS_MOCAP_OT_validate_armature(bpy.types.Operator):
    bl_idname = "genesis_mocap.validate_armature"
    bl_label = "Validar huesos Genesis"
    bl_description = "Comprueba los huesos Genesis requeridos por el perfil de 58 destinos"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        armature = getattr(context.scene, "genesis_mocap_armature", None)
        return armature is not None and armature.type == "ARMATURE"

    def execute(self, context):
        armature = context.scene.genesis_mocap_armature
        try:
            report = validate_armature_object(armature)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if report.is_valid:
            self.report(
                {"INFO"},
                "Genesis válido: {}/{} huesos requeridos. Perfil: 58 destinos (incluye controles auxiliares).".format(
                    report.found_count, report.required_bones
                ),
            )
            return {"FINISHED"}

        preview = ", ".join(report.missing_bones[:8])
        if report.missing_count > 8:
            preview += ", ..."
        self.report(
            {"WARNING"},
            "Faltan {}/{} huesos requeridos: {}".format(
                report.missing_count, report.required_bones, preview
            ),
        )
        return {"FINISHED"}
