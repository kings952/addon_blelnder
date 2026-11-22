"""Read-only worker executed by Blender's embedded Python."""
import json
import sys
from pathlib import Path

import bpy


def output_path():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--output" not in args:
        raise RuntimeError("Falta el argumento --output")
    return Path(args[args.index("--output") + 1])


def vector(value):
    return [round(float(component), 6) for component in value]


def inspect_loaded_file():
    armatures = []
    for obj in sorted(bpy.data.objects, key=lambda item: item.name.lower()):
        if obj.type != "ARMATURE":
            continue
        bones = []
        details = []
        for bone in obj.data.bones:
            bones.append(bone.name)
            details.append({
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "use_deform": bool(bone.use_deform),
                "head_local": vector(bone.head_local),
                "tail_local": vector(bone.tail_local),
                "length": round(float(bone.length), 6),
            })
        armatures.append({
            "name": obj.name,
            "data_name": obj.data.name,
            "bone_count": len(bones),
            "bones": bones,
            "bone_details": details,
            "pose_position": obj.data.pose_position,
            "is_library_linked": obj.library is not None,
        })
    return {
        "blend_file": bpy.data.filepath,
        "blender_version": bpy.app.version_string,
        "armature_count": len(armatures),
        "armatures": armatures,
        "object_count": len(bpy.data.objects),
    }


if __name__ == "__main__":
    destination = output_path()
    destination.write_text(
        json.dumps(inspect_loaded_file(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
