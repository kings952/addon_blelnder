"""Genesis Mocap add-on for Blender 5.x."""

bl_info = {
    "name": "Genesis Mocap",
    "author": "Genesis Mocap contributors",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Genesis Mocap",
    "description": "Base de interfaz y validación de esqueletos Genesis",
    "category": "Animation",
}


def register():
    # Blender-only imports stay inside register so the pure core is testable
    # from a regular Python virtual environment without bpy installed.
    import bpy
    from bpy.props import PointerProperty

    from .operators import CLASSES as OPERATOR_CLASSES
    from .ui import CLASSES as UI_CLASSES

    classes = OPERATOR_CLASSES + UI_CLASSES
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.genesis_mocap_armature = PointerProperty(
        name="Genesis Armature",
        description="Armature Genesis que se validará en esta escena",
        type=bpy.types.Object,
        poll=lambda _self, obj: obj is not None and obj.type == "ARMATURE",
    )


def unregister():
    import bpy

    from .operators import CLASSES as OPERATOR_CLASSES
    from .ui import CLASSES as UI_CLASSES

    if hasattr(bpy.types.Scene, "genesis_mocap_armature"):
        del bpy.types.Scene.genesis_mocap_armature

    for cls in reversed(OPERATOR_CLASSES + UI_CLASSES):
        bpy.utils.unregister_class(cls)
