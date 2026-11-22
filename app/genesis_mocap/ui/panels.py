"""Genesis Mocap sidebar panel."""

import bpy

from ..core.armature_validator import validate_armature_object


class GENESIS_MOCAP_PT_main(bpy.types.Panel):
    bl_label = "Genesis Mocap"
    bl_idname = "GENESIS_MOCAP_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Genesis Mocap"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Fase 1 · Base y validación", icon="ARMATURE_DATA")
        layout.prop(scene, "genesis_mocap_armature", text="Armature")

        armature = scene.genesis_mocap_armature
        if armature is None:
            layout.label(text="Selecciona un Armature Genesis.", icon="INFO")
            return
        if armature.type != "ARMATURE":
            layout.label(text="El objeto debe ser de tipo Armature.", icon="ERROR")
            return

        try:
            report = validate_armature_object(armature)
        except ValueError:
            layout.label(text="No se pudo validar el Armature.", icon="ERROR")
            return

        column = layout.column(align=True)
        column.label(text="Perfil: 58 destinos")
        column.label(text="Huesos Genesis: {}/{}".format(report.found_count, report.required_bones))
        column.label(text="Controles auxiliares: {}".format(len(report.auxiliary_targets)))
        if report.is_valid:
            column.label(text="Estructura completa", icon="CHECKMARK")
        else:
            column.label(text="Faltan {} huesos".format(report.missing_count), icon="ERROR")

        layout.operator("genesis_mocap.validate_armature", icon="CHECKMARK")
