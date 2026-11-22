"""Fase 3: solver 3D, calibración A/T y Swing-Twist para Genesis 3 Female.

Ejecutable independiente dentro del tester:
    python -m genesis_mocap_tester.phase3

La salida es una previsualización matemática de rotaciones relativas. Para obtener
rotaciones Blender exactas por hueso se necesita leer las matrices/rest roll del
armature .blend; no se inventan ejes locales ni se escribe en el archivo.
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass


# Quaternion convention: (w, x, y, z); composition qA*qB applies qB then qA.
EPS = 1e-9
LANDMARKS = {
    "nose": 0, "left_eye_inner": 1, "left_eye": 2, "left_eye_outer": 3,
    "right_eye_inner": 4, "right_eye": 5, "right_eye_outer": 6,
    "left_ear": 7, "right_ear": 8, "mouth_left": 9, "mouth_right": 10,
    "left_shoulder": 11, "right_shoulder": 12, "left_elbow": 13,
    "right_elbow": 14, "left_wrist": 15, "right_wrist": 16,
    "left_pinky": 17, "right_pinky": 18, "left_index": 19,
    "right_index": 20, "left_thumb": 21, "right_thumb": 22,
    "left_hip": 23, "right_hip": 24, "left_knee": 25,
    "right_knee": 26, "left_ankle": 27, "right_ankle": 28,
    "left_heel": 29, "right_heel": 30, "left_foot_index": 31,
    "right_foot_index": 32,
}

# This is the supplied Genesis3Female hierarchy, not a guessed generic rig.
GENESIS_PARENT = {
    "hip": "Genesis3Female", "pelvis": "hip", "abdomenLower": "hip",
    "abdomenUpper": "abdomenLower", "chestLower": "abdomenUpper",
    "chestUpper": "chestLower", "neckLower": "chestUpper",
    "neckUpper": "neckLower", "Head": "neckUpper",
    "lThighBend": "pelvis", "lThighTwist": "lThighBend",
    "lShin": "lThighBend", "lFoot": "lShin",
    "rThighBend": "pelvis", "rThighTwist": "rThighBend",
    "rShin": "rThighBend", "rFoot": "rShin",
    "lCollar": "chestUpper", "lShldrBend": "lCollar",
    "lShldrTwist": "lShldrBend", "lForearmBend": "lShldrBend",
    "lForearmTwist": "lForearmBend", "lHand": "lForearmBend",
    "rCollar": "chestUpper", "rShldrBend": "rCollar",
    "rShldrTwist": "rShldrBend", "rForearmBend": "rShldrBend",
    "rForearmTwist": "rForearmBend", "rHand": "rForearmBend",
    "lFoot": "lShin", "rFoot": "rShin",
    "lMetatarsals": "lFoot", "rMetatarsals": "rFoot",
    "lToe": "lMetatarsals", "rToe": "rMetatarsals",
}
# 33-point MediaPipe Pose does not observe Genesis fingers, face, breasts,
# nipples, heels/toe phalanges, or twist axes. Those bones are deliberately
# listed as unsupported instead of receiving fabricated rotations.
GENESIS_133_GROUPS = {
    "root/pelvis/spine": ("hip", "pelvis", "abdomenLower", "abdomenUpper", "chestLower", "chestUpper"),
    "neck/head": ("neckLower", "neckUpper", "Head"),
    "arms": ("lCollar", "lShldrBend", "lShldrTwist", "lForearmBend", "lForearmTwist", "lHand",
             "rCollar", "rShldrBend", "rShldrTwist", "rForearmBend", "rForearmTwist", "rHand"),
    "legs": ("lThighBend", "lThighTwist", "lShin", "lFoot",
             "rThighBend", "rThighTwist", "rShin", "rFoot"),
}
SEGMENTS = (
    # Genesis bone, MediaPipe start/end, canonical local direction, twist axis.
    ("lShldrBend", 11, 13, (1, 0, 0)),
    ("lForearmBend", 13, 15, (1, 0, 0)),
    ("rShldrBend", 12, 14, (-1, 0, 0)),
    ("rForearmBend", 14, 16, (-1, 0, 0)),
    ("lThighBend", 23, 25, (0, 0, -1)),
    ("lShin", 25, 27, (0, 0, -1)),
    ("rThighBend", 24, 26, (0, 0, -1)),
    ("rShin", 26, 28, (0, 0, -1)),
    ("chestUpper", 23, 11, (0, 1, 0)),
    ("neckUpper", 11, 0, (0, 1, 0)),
    ("lFoot", 29, 31, (0, 1, 0)),
    ("rFoot", 30, 32, (0, 1, 0)),
)


def v_add(a, b): return tuple(x + y for x, y in zip(a, b))
def v_sub(a, b): return tuple(x - y for x, y in zip(a, b))
def v_scale(a, s): return tuple(x * s for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(v): return math.sqrt(dot(v, v))
def normalize(v):
    n = norm(v)
    if n < EPS: raise ValueError("Vector de longitud cero")
    return tuple(x / n for x in v)


def q_normalize(q):
    n = math.sqrt(sum(x*x for x in q))
    if n < EPS: raise ValueError("Quaternion nulo")
    return tuple(x / n for x in q)


def q_conjugate(q): return (q[0], -q[1], -q[2], -q[3])


def q_mul(a, b):
    aw, ax, ay, az = a; bw, bx, by, bz = b
    return (
        aw*bw-ax*bx-ay*by-az*bz,
        aw*bx+ax*bw+ay*bz-az*by,
        aw*by-ax*bz+ay*bw+az*bx,
        aw*bz+ax*by-ay*bx+az*bw,
    )


def q_rotate(q, v):
    q = q_normalize(q)
    p = (0.0, v[0], v[1], v[2])
    r = q_mul(q_mul(q, p), q_conjugate(q))
    return (r[1], r[2], r[3])


def q_from_axis_angle(axis, angle):
    axis = normalize(axis); h = angle * 0.5
    return q_normalize((math.cos(h), axis[0]*math.sin(h), axis[1]*math.sin(h), axis[2]*math.sin(h)))


def q_from_to(source, target):
    """Shortest rotation source -> target, including the antiparallel case."""
    a, b = normalize(source), normalize(target)
    d = max(-1.0, min(1.0, dot(a, b)))
    if d > 1.0 - 1e-8: return (1.0, 0.0, 0.0, 0.0)
    if d < -1.0 + 1e-8:
        candidate = cross(a, (1.0, 0.0, 0.0))
        if norm(candidate) < 1e-7: candidate = cross(a, (0.0, 1.0, 0.0))
        return q_from_axis_angle(candidate, math.pi)
    c = cross(a, b)
    return q_normalize((1.0 + d, c[0], c[1], c[2]))


def swing_twist_decomposition(q, twist_axis):
    """Return swing, twist where q == swing * twist (up to quaternion sign)."""
    q = q_normalize(q); axis = normalize(twist_axis)
    projection = v_scale(axis, dot((q[1], q[2], q[3]), axis))
    raw_twist = (q[0], projection[0], projection[1], projection[2])
    if math.sqrt(sum(x*x for x in raw_twist)) < 1e-8:
        twist = (1.0, 0.0, 0.0, 0.0)
    else:
        twist = q_normalize(raw_twist)
    swing = q_normalize(q_mul(q, q_conjugate(twist)))
    return swing, twist


def _point(landmarks, index, threshold):
    if index >= len(landmarks): return None
    p = landmarks[index]
    if len(p) < 4 or float(p[3]) < threshold: return None
    # MediaPipe x/y are normalized image coordinates; z is relative depth.
    # Flip y to make an upward-positive camera-space vector.
    return (float(p[0]), -float(p[1]), float(p[2]))


@dataclass
class BoneRotation:
    bone: str
    quaternion: tuple
    swing: tuple
    twist: tuple
    visibility: float
    euler_degrees: tuple


def _q_to_euler_degrees(q):
    w, x, y, z = q_normalize(q)
    sinr = 2*(w*x + y*z); cosr = 1 - 2*(x*x + y*y)
    roll = math.atan2(sinr, cosr)
    sinp = 2*(w*y - z*x)
    pitch = math.copysign(math.pi/2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
    siny = 2*(w*z + x*y); cosy = 1 - 2*(y*y + z*z)
    yaw = math.atan2(siny, cosy)
    return tuple(round(math.degrees(a), 2) for a in (roll, pitch, yaw))


class GenesisRetargetSolver:
    """Pose solver relative to a captured neutral pose.

    Segment quaternions are camera-space direction deltas. They are not yet
    Blender pose-bone local quaternions: exact conversion requires each bone's
    rest matrix, roll, parent matrix and chosen Blender coordinate convention.
    """
    def __init__(self, min_visibility=0.35):
        self.min_visibility = float(min_visibility)
        self.calibration = None
        self.calibration_label = None

    def solve_raw(self, landmarks):
        results = {}
        for bone, start, end, local_axis in SEGMENTS:
            a, b = _point(landmarks, start, self.min_visibility), _point(landmarks, end, self.min_visibility)
            if a is None or b is None: continue
            direction = v_sub(b, a)
            if norm(direction) < 1e-6: continue
            results[bone] = (q_from_to(local_axis, direction), min(float(landmarks[start][3]), float(landmarks[end][3])))
        return results

    def calibrate(self, landmarks, label="A-Pose"):
        raw = self.solve_raw(landmarks)
        if len(raw) < 6:
            raise ValueError("Calibración insuficiente: se necesitan al menos 6 segmentos visibles; encuadra hombros, codos, caderas y rodillas.")
        self.calibration = raw
        self.calibration_label = label
        return len(raw)

    def solve(self, landmarks):
        raw = self.solve_raw(landmarks)
        if self.calibration is None:
            return {}, raw
        output = {}
        for bone, (current, visibility) in raw.items():
            if bone not in self.calibration: continue
            neutral = self.calibration[bone][0]
            delta = q_normalize(q_mul(current, q_conjugate(neutral)))
            axis = next(s[4] for s in SEGMENTS if s[0] == bone)
            swing, twist = swing_twist_decomposition(delta, axis)
            output[bone] = BoneRotation(bone, delta, swing, twist, visibility, _q_to_euler_degrees(delta))
        return output, raw


def run_self_tests():
    identity = (1.0, 0.0, 0.0, 0.0)
    assert q_rotate(identity, (1, 2, 3)) == (1, 2, 3)
    q = q_from_to((1, 0, 0), (0, 1, 0))
    assert norm(v_sub(q_rotate(q, (1, 0, 0)), (0, 1, 0))) < 1e-6
    qa = q_from_to((0, 0, 1), (0, 0, -1))
    assert norm(v_sub(q_rotate(qa, (0, 0, 1)), (0, 0, -1))) < 1e-6
    original = q_from_axis_angle((0, 0, 1), 1.1)
    swing, twist = swing_twist_decomposition(original, (0, 0, 1))
    rebuilt = q_normalize(q_mul(swing, twist))
    assert abs(abs(dot(original, rebuilt)) - 1.0) < 1e-6
    neutral = [(0.0, 0.0, 0.0, 1.0) for _ in range(33)]
    # Synthetic body with distinct segment endpoints.
    pts = {
        11:(-.3,.2,0,1), 13:(-.5,.1,0,1), 15:(-.7,0,0,1),
        12:(.3,.2,0,1), 14:(.5,.1,0,1), 16:(.7,0,0,1),
        23:(-.2,-.2,0,1), 25:(-.2,-.5,0,1), 27:(-.2,-.8,0,1),
        24:(.2,-.2,0,1), 26:(.2,-.5,0,1), 28:(.2,-.8,0,1),
        29:(-.2,-.8,0,1), 31:(-.2,-.9,0,1), 30:(.2,-.8,0,1), 32:(.2,-.9,0,1),
        0:(0,.45,0,1),
    }
    for i, p in pts.items(): neutral[i] = p
    solver = GenesisRetargetSolver()
    count = solver.calibrate(neutral, "T-Pose")
    solved, _ = solver.solve(neutral)
    assert count >= 6 and solved
    assert max(abs(v) for item in solved.values() for v in item.euler_degrees) < 1e-5
    # Low visibility must suppress a segment.
    neutral[13] = (neutral[13][0], neutral[13][1], neutral[13][2], 0.01)
    assert "lShldrBend" not in solver.solve_raw(neutral)
    return True


class Phase3Window:
    def __init__(self, root):
        self.root = root
        root.title("Genesis Mocap · Fase 3 Solver / Retargeting")
        root.geometry("1080x720"); root.minsize(820, 560)
        self.solver = GenesisRetargetSolver()
        self.detector = None; self.image = None; self.detections = []
        self.threshold = tk.DoubleVar(value=0.35)
        self.mode = tk.StringVar(value="A-Pose")
        self.status = tk.StringVar(value="Carga una fotografía de cuerpo completo para comenzar.")
        self._build()

    def _build(self):
        outer = ttk.Frame(self.root, padding=12); outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Fase 3 · Solver 3D para Genesis3Female (Root Node · 133 huesos)",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Landmarks MediaPipe 33 → segmentos Genesis observables → calibración → delta quaternion → Swing/Twist.",
                  wraplength=1000).pack(anchor="w", pady=5)
        bar = ttk.Frame(outer); bar.pack(fill="x", pady=6)
        ttk.Button(bar, text="Abrir imagen y detectar pose…", command=self.open_image).pack(side="left")
        ttk.Label(bar, text="Visibilidad mínima").pack(side="left", padx=(18, 4))
        ttk.Spinbox(bar, from_=0.1, to=0.95, increment=0.05, textvariable=self.threshold, width=6,
                    command=self._update_threshold).pack(side="left")
        ttk.Label(bar, text="Pose neutra").pack(side="left", padx=(18, 4))
        ttk.Combobox(bar, textvariable=self.mode, values=("A-Pose", "T-Pose"), state="readonly", width=10).pack(side="left")
        ttk.Button(bar, text="Calibrar pose actual", command=self.calibrate).pack(side="left", padx=5)
        ttk.Button(bar, text="Limpiar calibración", command=self.clear_calibration).pack(side="left")
        ttk.Button(bar, text="Resolver", command=self.solve).pack(side="left", padx=5)
        self.output = tk.Text(outer, wrap="none", font=("Consolas", 9))
        sy = ttk.Scrollbar(outer, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=sy.set)
        self.output.pack(side="left", fill="both", expand=True); sy.pack(side="right", fill="y")
        self._write("MAPA GENESIS ROOT NODE\n133 huesos declarados en el rig. El detector Pose 33 solo observa el cuerpo principal.\n\n"
                    "Cadenas del rig: hip → pelvis/abdomenLower; abdomenLower → abdomenUpper → chestLower → chestUpper → cuello/cabeza; "
                    "piernas desde pelvis; brazos desde chestUpper → collar → hombro → antebrazo → mano.\n"
                    "No se asignan rotaciones inventadas a dedos, cara, lengua, orejas, pectorales ni pezones.\n\n"
                    "Carga una imagen para obtener landmarks 3D relativos y probar el solver.")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _write(self, text):
        self.output.delete("1.0", "end"); self.output.insert("1.0", text)

    def _update_threshold(self):
        self.solver.min_visibility = float(self.threshold.get())

    def open_image(self):
        path = filedialog.askopenfilename(parent=self.root, filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if not path: return
        try:
            import cv2
            self._update_threshold()
            if self.detector is None:
                from .vision import MultiPersonPoseDetector
                self.detector = MultiPersonPoseDetector()
            self.image = cv2.imread(path)
            if self.image is None: raise RuntimeError("No se pudo abrir la imagen.")
            self.detections = self.detector.detect_image(self.image)
            if not self.detections: raise RuntimeError("MediaPipe no detectó una pose.")
            self._write("Imagen: {}\nPersonas: {}\n\n".format(path, len(self.detections)) +
                        "Selecciona la persona 1..{} escribiendo el índice en el selector de abajo.".format(len(self.detections)))
            self.person_index.set("1")
            self._show_detection()
            self.status.set("{} persona(s) detectada(s).".format(len(self.detections)))
        except Exception as exc:
            messagebox.showerror("Fase 3", str(exc), parent=self.root)
            self.status.set("Error al detectar pose.")

    def _show_detection(self):
        try: index = max(0, min(len(self.detections)-1, int(self.person_index.get())-1))
        except ValueError: index = 0
        self.current_landmarks = self.detections[index]["landmarks"]
        self._write("SUJETO {} · track {}\n".format(index+1, self.detections[index]["track_id"]) +
                    "Landmarks detectados: {} / 33\nVisibilidad media: {:.1f}%\n".format(
                        self.detections[index]["visible_landmarks"], self.detections[index]["mean_visibility"]*100) +
                    "\nCalibración: {}\n".format(self.solver.calibration_label or "sin calibrar") +
                    "Usa Calibrar pose actual en A-Pose o T-Pose y luego Resolver.")
        
    def calibrate(self):
        if not hasattr(self, "current_landmarks"):
            messagebox.showwarning("Fase 3", "Primero carga una imagen.", parent=self.root); return
        self._update_threshold()
        try:
            n = self.solver.calibrate(self.current_landmarks, self.mode.get())
            self._write("CALIBRACIÓN {} COMPLETADA\nSegmentos guardados: {}\n\n".format(self.mode.get(), n) +
                        "La pose capturada se toma como cero. Carga una segunda imagen con movimiento y pulsa Resolver.")
            self.status.set("Calibración {} lista.".format(self.mode.get()))
        except ValueError as exc:
            messagebox.showwarning("Calibración", str(exc), parent=self.root)

    def solve(self):
        if not hasattr(self, "current_landmarks"):
            messagebox.showwarning("Fase 3", "Primero carga una imagen.", parent=self.root); return
        if self.solver.calibration is None:
            messagebox.showwarning("Fase 3", "Captura primero una A-Pose o T-Pose neutra.", parent=self.root); return
        self._update_threshold()
        rotations, raw = self.solver.solve(self.current_landmarks)
        lines = ["RESULTADO DEL SOLVER · Genesis3Female / Root Node", "Huesos con segmento visible: {}".format(len(raw)),
                 "Rotaciones relativas calculadas: {}".format(len(rotations)), ""]
        for name, item in sorted(rotations.items()):
            lines.append("{} | Euler XYZ aprox. {}° | vis {:.0f}%".format(name, item.euler_degrees, item.visibility*100))
            lines.append("  q={}".format(tuple(round(v, 5) for v in item.quaternion)))
            lines.append("  swing={} twist={}".format(
                tuple(round(v, 4) for v in item.swing), tuple(round(v, 4) for v in item.twist)))
        lines += ["", "LIMITACIÓN IMPORTANTE",
                  "Estas son rotaciones relativas de dirección en el espacio de cámara, no pose-bone local Blender.",
                  "Para retargeting local exacto se necesita el .blend real y las matrices de reposo/roll de los 133 huesos.",
                  "Twist bones, dedos y cara no reciben valores porque MediaPipe Pose no aporta esos landmarks."]
        self._write("\n".join(lines)); self.status.set("Solver terminado · {} huesos.".format(len(rotations)))

    def clear_calibration(self):
        self.solver.calibration = None; self.solver.calibration_label = None
        self.status.set("Calibración eliminada.")
        self._write("Calibración eliminada. Carga una imagen A-Pose o T-Pose para comenzar de nuevo.")

    def close(self):
        if self.detector is not None: self.detector.close()
        self.root.destroy()


def main():
    run_self_tests()
    root = tk.Tk()
    window = Phase3Window(root)
    ttk.Label(root, textvariable=window.status, relief="sunken", anchor="w").pack(side="bottom", fill="x")
    # Subject selector is placed in the main window footer for multi-person stills.
    row = ttk.Frame(root); row.pack(side="bottom", fill="x", padx=12, pady=3)
    ttk.Label(row, text="Persona detectada (índice):").pack(side="left")
    window.person_index = tk.StringVar(value="1")
    ttk.Spinbox(row, from_=1, to=8, textvariable=window.person_index, width=5,
                command=window._show_detection).pack(side="left", padx=5)
    root.mainloop()


if __name__ == "__main__":
    main()
