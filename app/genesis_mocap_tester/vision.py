"""MediaPipe multi-person pose detection for video and still images."""
from __future__ import annotations

import math
import os
import urllib.request
from pathlib import Path

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

# MediaPipe Pose's 33-landmark topology (pairs of landmark indexes).
POSE_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27), (27, 29), (29, 31),
    (27, 31), (24, 26), (26, 28), (28, 30), (30, 32), (28, 32),
)


def default_model_path():
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GenesisMocap" / "models" / "pose_landmarker_lite.task"


def ensure_pose_model(model_path=None):
    path = Path(model_path).expanduser() if model_path else default_model_path()
    if path.is_file() and path.stat().st_size > 100_000:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".download")
    try:
        request = urllib.request.Request(MODEL_URL, headers={"User-Agent": "GenesisMocap/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response, temp.open("wb") as target:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
        if temp.stat().st_size < 100_000:
            raise RuntimeError("El modelo descargado está incompleto.")
        temp.replace(path)
    except Exception as exc:
        temp.unlink(missing_ok=True)
        raise RuntimeError(
            "No se pudo obtener el modelo MediaPipe. Comprueba Internet o coloca "
            "pose_landmarker_lite.task en {}. Detalle: {}".format(path, exc)
        ) from exc
    return path


class PersonTracker:
    """Assign temporary track IDs using normalized bounding-box centers."""

    def __init__(self, max_distance=0.20):
        self.max_distance = max_distance
        self._tracks = {}
        self._next_id = 1

    def update(self, detections):
        available, updated, output = set(self._tracks), {}, []
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            center = detection.get("center", ((x1 + x2) / 2, (y1 + y2) / 2))
            best_id, best_distance = None, self.max_distance
            for track_id in available:
                distance = math.dist(center, self._tracks[track_id])
                if distance < best_distance:
                    best_id, best_distance = track_id, distance
            if best_id is None:
                best_id = self._next_id
                self._next_id += 1
            else:
                available.remove(best_id)
            updated[best_id] = center
            item = dict(detection)
            item["track_id"] = best_id
            output.append(item)
        self._tracks = updated
        return output


class MultiPersonPoseDetector:
    """PoseLandmarker with separate VIDEO and IMAGE modes."""

    def __init__(self, model_path=None, max_people=8, min_detection_confidence=0.5):
        self.model_path = ensure_pose_model(model_path)
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError("MediaPipe no está instalado. Ejecuta: pip install -r requirements.txt") from exc
        self._python = python
        self._vision = vision
        self._mp = mp
        self.max_people = max(1, int(max_people))
        self.min_detection_confidence = float(min_detection_confidence)
        self._video_landmarker = self._create_landmarker(vision.RunningMode.VIDEO)
        self._image_landmarker = self._create_landmarker(vision.RunningMode.IMAGE)
        self._last_timestamp = -1
        self._tracker = PersonTracker()

    def _create_landmarker(self, mode):
        options = self._vision.PoseLandmarkerOptions(
            base_options=self._python.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=mode,
            num_poses=self.max_people,
            min_pose_detection_confidence=self.min_detection_confidence,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        return self._vision.PoseLandmarker.create_from_options(options)

    def _to_mp_image(self, frame_bgr):
        import cv2
        import numpy as np
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=np.asarray(rgb))

    def _convert_result(self, result, frame_bgr):
        height, width = frame_bgr.shape[:2]
        detections = []
        for pose in result.pose_landmarks:
            visible = [p for p in pose if getattr(p, "visibility", 1.0) >= 0.25]
            if not visible:
                continue
            xs = [min(1.0, max(0.0, float(p.x))) for p in visible]
            ys = [min(1.0, max(0.0, float(p.y))) for p in visible]
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            if (x2 - x1) * (y2 - y1) < 0.0005:
                continue
            landmarks = [
                (float(p.x), float(p.y), float(p.z), float(getattr(p, "visibility", 1.0)))
                for p in pose
            ]
            detections.append({
                "bbox": (int(x1 * width), int(y1 * height), int(x2 * width), int(y2 * height)),
                "center": ((x1 + x2) / 2, (y1 + y2) / 2),
                "landmarks": landmarks,
                "visible_landmarks": len(visible),
                "mean_visibility": sum(p[3] for p in landmarks) / len(landmarks),
            })
        return self._tracker.update(detections)

    def detect(self, frame_bgr, timestamp_ms):
        """Detect poses in a video/camera frame."""
        timestamp_ms = max(int(timestamp_ms), self._last_timestamp + 1)
        self._last_timestamp = timestamp_ms
        result = self._video_landmarker.detect_for_video(self._to_mp_image(frame_bgr), timestamp_ms)
        return self._convert_result(result, frame_bgr)

    def detect_image(self, image_bgr):
        """Detect poses once in a still image (IMAGE mode; no timestamp required)."""
        result = self._image_landmarker.detect(self._to_mp_image(image_bgr))
        return self._convert_result(result, image_bgr)

    def close(self):
        self._video_landmarker.close()
        self._image_landmarker.close()
