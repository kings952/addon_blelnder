"""Canonical Genesis source-bone mapping from the project TDD."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class BoneMapping:
    index: int
    target_name: str
    genesis_name: Optional[str]


# None marks auxiliary controls that do not receive direct base-tracking rotation.
GENESIS_BONE_MAP: Tuple[BoneMapping, ...] = (
    BoneMapping(1, "Hips", "pelvis"),
    BoneMapping(2, "Spine", "abdomenLower"),
    BoneMapping(3, "Chest", "chestLower"),
    BoneMapping(4, "UpperChest", "chestUpper"),
    BoneMapping(5, "Neck", "neckLower"),
    BoneMapping(6, "Head", "neckUpper"),
    BoneMapping(7, "RightUpperLeg", "rThighBend"),
    BoneMapping(8, "RightLowerLeg", "rShin"),
    BoneMapping(9, "RightFoot", "rFoot"),
    BoneMapping(10, "RightToes", "rToe"),
    BoneMapping(11, "RightLegBendGoal", None),
    BoneMapping(12, "LeftUpperLeg", "lThighBend"),
    BoneMapping(13, "LeftLowerLeg", "lShin"),
    BoneMapping(14, "LeftFoot", "lFoot"),
    BoneMapping(15, "LeftToes", "lToe"),
    BoneMapping(16, "LeftLegBendGoal", None),
    BoneMapping(17, "RightEye", None),
    BoneMapping(18, "LeftEye", None),
    BoneMapping(19, "RightShoulder", "rShldrBend"),
    BoneMapping(20, "RightUpperArm", "rShldrTwist"),
    BoneMapping(21, "RightLowerArm", "rForearmBend"),
    BoneMapping(22, "RightHand", "rHand"),
    BoneMapping(23, "RightArmBendGoal", None),
    BoneMapping(24, "LeftShoulder", "lShldrBend"),
    BoneMapping(25, "LeftUpperArm", "lShldrTwist"),
    BoneMapping(26, "LeftLowerArm", "lForearmBend"),
    BoneMapping(27, "LeftHand", "lHand"),
    BoneMapping(28, "LeftArmBendGoal", None),
    BoneMapping(29, "RightLittleProximal", "rPinky1"),
    BoneMapping(30, "RightLittleIntermediate", "rPinky2"),
    BoneMapping(31, "RightLittleDistal", "rPinky3"),
    BoneMapping(32, "RightRingProximal", "rRing1"),
    BoneMapping(33, "RightRingIntermediate", "rRing2"),
    BoneMapping(34, "RightRingDistal", "rRing3"),
    BoneMapping(35, "RightMiddleProximal", "rMid1"),
    BoneMapping(36, "RightMiddleIntermediate", "rMid2"),
    BoneMapping(37, "RightMiddleDistal", "rMid3"),
    BoneMapping(38, "RightIndexProximal", "rIndex1"),
    BoneMapping(39, "RightIndexIntermediate", "rIndex2"),
    BoneMapping(40, "RightIndexDistal", "rIndex3"),
    BoneMapping(41, "RightThumbProximal", "rThumb1"),
    BoneMapping(42, "RightThumbIntermediate", "rThumb2"),
    BoneMapping(43, "RightThumbDistal", "rThumb3"),
    BoneMapping(44, "LeftLittleProximal", "lPinky1"),
    BoneMapping(45, "LeftLittleIntermediate", "lPinky2"),
    BoneMapping(46, "LeftLittleDistal", "lPinky3"),
    BoneMapping(47, "LeftRingProximal", "lRing1"),
    BoneMapping(48, "LeftRingIntermediate", "lRing2"),
    BoneMapping(49, "LeftRingDistal", "lRing3"),
    BoneMapping(50, "LeftMiddleProximal", "lMid1"),
    BoneMapping(51, "LeftMiddleIntermediate", "lMid2"),
    BoneMapping(52, "LeftMiddleDistal", "lMid3"),
    BoneMapping(53, "LeftIndexProximal", "lIndex1"),
    BoneMapping(54, "LeftIndexIntermediate", "lIndex2"),
    BoneMapping(55, "LeftIndexDistal", "lIndex3"),
    BoneMapping(56, "LeftThumbProximal", "lThumb1"),
    BoneMapping(57, "LeftThumbIntermediate", "lThumb2"),
    BoneMapping(58, "LeftThumbDistal", "lThumb3"),
)

EXPECTED_TARGET_BONES = 58
REQUIRED_GENESIS_BONES = tuple(
    item.genesis_name for item in GENESIS_BONE_MAP if item.genesis_name is not None
)
AUXILIARY_TARGET_BONES = tuple(
    item.target_name for item in GENESIS_BONE_MAP if item.genesis_name is None
)
