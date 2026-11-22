"""Blender-independent validation of a Genesis armature bone-name set."""

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Tuple

from .bone_mapping import (
    AUXILIARY_TARGET_BONES,
    EXPECTED_TARGET_BONES,
    REQUIRED_GENESIS_BONES,
)


@dataclass(frozen=True)
class ArmatureValidation:
    total_targets: int
    required_bones: int
    found_bones: Tuple[str, ...]
    missing_bones: Tuple[str, ...]
    auxiliary_targets: Tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.missing_bones

    @property
    def found_count(self) -> int:
        return len(self.found_bones)

    @property
    def missing_count(self) -> int:
        return len(self.missing_bones)

    @property
    def percentage(self) -> float:
        if not self.required_bones:
            return 100.0
        return self.found_count * 100.0 / self.required_bones


def validate_genesis_bones(bone_names: Iterable[str]) -> ArmatureValidation:
    """Validate required Genesis source bones; auxiliary targets are informational."""
    available: FrozenSet[str] = frozenset(bone_names)
    found = tuple(name for name in REQUIRED_GENESIS_BONES if name in available)
    missing = tuple(name for name in REQUIRED_GENESIS_BONES if name not in available)

    return ArmatureValidation(
        total_targets=EXPECTED_TARGET_BONES,
        required_bones=len(REQUIRED_GENESIS_BONES),
        found_bones=found,
        missing_bones=missing,
        auxiliary_targets=AUXILIARY_TARGET_BONES,
    )


def validate_armature_object(armature_object) -> ArmatureValidation:
    """Adapt a Blender Object of type ARMATURE to the pure validator."""
    if armature_object is None or getattr(armature_object, "type", None) != "ARMATURE":
        raise ValueError("El objeto seleccionado no es un Armature.")
    return validate_genesis_bones(bone.name for bone in armature_object.data.bones)
