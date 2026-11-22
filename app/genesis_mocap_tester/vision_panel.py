"""Camera, video and still-image pose preview with selectable people."""
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class VisionCapturePanel:
    def __init__(self, parent):
        import cv2
        self.cv2 = cv2
        self.parent = parent
        self.capture = None
        self.detector = None
        self.running = False
        self.frame_index = 0
        self.selected_track = None
        self.photo = None
        self.still_frame = None
        self.still_detections = []
        self.source_path = tk.StringVar()
        self.camera_index = tk.StringVar(value="0")
        self.model_path = tk.StringVar()
        self.max_people = tk.IntVar(value=8)
        self.show_skeleton = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Abre una imagen, vídeo o conecta una cámara.")
        self._build()

    def _build(self):
        outer = ttk.Frame(self.parent, padding=10)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Fase 2 · Motor de Visión", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Analiza imágenes estáticas, vídeos y cámara. Selecciona una persona para revisar su pose y visibilidad.",
            wraplength=1000,
        ).pack(anchor="w", pady=5)

        source = ttk.LabelFrame(outer, text="Fuente de captura", padding=8)
        source.pack(fill="x")
        row = ttk.Frame(source)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Imagen", width=18).pack(side="left")
        ttk.Button(row, text="Abrir imagen...", command=self._choose_image).pack(side="left")
        ttk.Label(row, text="Formatos: PNG, JPG, JPEG, BMP, WEBP").pack(side="left", padx=8)

        row = ttk.Frame(source)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Vídeo", width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.source_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="Abrir vídeo...", command=self._choose_video).pack(side="left")

        row = ttk.Frame(source)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Cámara (índice)", width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.camera_index, width=8).pack(side="left", padx=4)
        ttk.Button(row, text="Conectar cámara", command=self.open_camera).pack(side="left")
        ttk.Label(row, text="Máx. personas").pack(side="left", padx=(18, 4))
        ttk.Spinbox(row, from_=1, to=20, textvariable=self.max_people, width=5).pack(side="left")
        ttk.Checkbutton(row, text="Dibujar esqueleto", variable=self.show_skeleton, command=self._refresh_still).pack(side="left", padx=12)

        row = ttk.Frame(source)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Modelo .task (opcional)", width=22).pack(side="left")
        ttk.Entry(row, textvariable=self.model_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="Buscar...", command=self._choose_model).pack(side="left")

        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=7)
        ttk.Button(actions, text="Iniciar / Reanudar", command=self.start).pack(side="left")
        ttk.Button(actions, text="Pausar", command=self.pause).pack(side="left", padx=5)
        ttk.Button(actions, text="Detener y liberar", command=self.stop).pack(side="left")
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=12)

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        preview = ttk.LabelFrame(body, text="Vista de detección y esqueleto", padding=5)
        preview.pack(side="left", fill="both", expand=True)
        self.preview = ttk.Label(preview, text="La vista de imagen/cámara/vídeo aparecerá aquí", anchor="center")
        self.preview.pack(fill="both", expand=True)

        side = ttk.LabelFrame(body, text="Personas detectadas", padding=8)
        side.pack(side="right", fill="y", padx=(8, 0))
        ttk.Label(side, text="Sujeto objetivo:").pack(anchor="w")
        self.subject = ttk.Combobox(side, state="readonly", width=27)
        self.subject.pack(fill="x", pady=5)
        self.subject.bind("<<ComboboxSelected>>", self._select_subject)
        self.people_list = tk.Listbox(side, width=31, height=10, exportselection=False)
        self.people_list.pack(fill="x", expand=False)
        self.people_list.bind("<<ListboxSelect>>", self._select_from_list)
        ttk.Label(side, text="Información del sujeto:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 3))
        self.details = tk.Text(side, width=34, height=13, wrap="word", state="disabled", font=("Consolas", 8))
        self.details.pack(fill="both", expand=True)
        ttk.Label(side, text="Verde = objetivo · Amarillo = otras personas", wraplength=230).pack(anchor="w", pady=8)

    def _choose_image(self):
        path = filedialog.askopenfilename(
            parent=self.parent,
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp"), ("Todos", "*.*")],
        )
        if path:
            self.open_image(path)

    def _choose_video(self):
        path = filedialog.askopenfilename(
            parent=self.parent,
            filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"), ("Todos", "*.*")],
        )
        if path:
            self.source_path.set(path)
            self.open_video(path)

    def _choose_model(self):
        path = filedialog.askopenfilename(
            parent=self.parent,
            filetypes=[("MediaPipe task", "*.task"), ("Todos", "*.*")],
        )
        if path:
            self.model_path.set(path)

    def _prepare_detector(self):
        if self.detector is None:
            from .vision import MultiPersonPoseDetector
            self.status.set("Cargando modelo (la primera ejecución puede descargarlo)...")
            self.parent.update_idletasks()
            self.detector = MultiPersonPoseDetector(
                self.model_path.get().strip() or None,
                self.max_people.get(),
            )

    def _release_capture(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def _reset_results(self):
        self.selected_track = None
        self.still_frame = None
        self.still_detections = []
        self.subject["values"] = []
        self.subject.set("")
        self.people_list.delete(0, "end")
        self._set_details("No hay una persona seleccionada.")

    def open_image(self, path):
        self.stop()
        frame = self.cv2.imread(path)
        if frame is None:
            messagebox.showerror("Imagen", "No se pudo abrir la imagen. Comprueba el formato.", parent=self.parent)
            return
        try:
            self._prepare_detector()
            detections = self.detector.detect_image(frame)
        except Exception as exc:
            messagebox.showerror("Motor de visión", str(exc), parent=self.parent)
            self.status.set("No se pudo analizar la imagen.")
            return
        self.still_frame = frame
        self.still_detections = detections
        self.selected_track = detections[0]["track_id"] if detections else None
        self._update_people(detections)
        self._render_still()
        self.status.set("Imagen analizada · {} persona(s) detectada(s).".format(len(detections)))

    def open_video(self, path):
        self.stop()
        cap = self.cv2.VideoCapture(path)
        if not cap.isOpened():
            cap.release()
            messagebox.showerror("Vídeo", "No se pudo abrir el vídeo.", parent=self.parent)
            return
        self.capture = cap
        self.frame_index = 0
        self.status.set("Vídeo cargado. Pulsa Iniciar / Reanudar.")

    def open_camera(self):
        self.stop()
        try:
            index = int(self.camera_index.get())
        except ValueError:
            messagebox.showerror("Cámara", "El índice debe ser un número entero.", parent=self.parent)
            return
        cap = self.cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            messagebox.showerror("Cámara", "No se pudo abrir la cámara {}. Revisa conexión y permisos.".format(index), parent=self.parent)
            return
        self.capture = cap
        self.frame_index = 0
        self.status.set("Cámara conectada. Pulsa Iniciar / Reanudar.")

    def start(self):
        if self.capture is None:
            messagebox.showwarning("Sin fuente", "Abre una imagen, un vídeo o conecta una cámara primero.", parent=self.parent)
            return
        try:
            self._prepare_detector()
        except Exception as exc:
            messagebox.showerror("Motor de visión", str(exc), parent=self.parent)
            self.status.set("No se pudo iniciar el detector.")
            return
        if not self.running:
            self.running = True
            self.status.set("Procesando captura...")
            self._tick()

    def pause(self):
        self.running = False
        if self.capture is not None:
            self.status.set("Captura pausada.")

    def stop(self):
        self.running = False
        self._release_capture()
        if self.detector is not None:
            self.detector.close()
            self.detector = None
        if hasattr(self, "subject"):
            self._reset_results()
            self.preview.configure(image="", text="La vista de imagen/cámara/vídeo aparecerá aquí")
            self.photo = None
        if hasattr(self, "status"):
            self.status.set("Captura detenida y recursos liberados.")

    def _select_subject(self, _event=None):
        try:
            self.selected_track = int(self.subject.get().split("·")[0].replace("Persona", "").strip())
        except (ValueError, IndexError):
            self.selected_track = None
        self._refresh_still()

    def _select_from_list(self, _event=None):
        selection = self.people_list.curselection()
        if selection:
            labels = list(self.subject["values"])
            if selection[0] < len(labels):
                self.subject.current(selection[0])
                self._select_subject()

    def _update_people(self, detections):
        labels = [
            "Persona {} · {:.0f}% vis.".format(d["track_id"], d.get("mean_visibility", 0.0) * 100)
            for d in detections
        ]
        self.subject["values"] = labels
        self.people_list.delete(0, "end")
        selected_index = None
        for index, (label, detection) in enumerate(zip(labels, detections)):
            self.people_list.insert("end", label)
            if detection["track_id"] == self.selected_track:
                selected_index = index
        if selected_index is None and detections:
            selected_index = 0
            self.selected_track = detections[0]["track_id"]
        if selected_index is not None:
            self.subject.current(selected_index)
            self.people_list.selection_set(selected_index)
        elif not detections:
            self.subject.set("")
        selected = next((d for d in detections if d["track_id"] == self.selected_track), None)
        self._set_details(self._format_details(selected) if selected else "No se detectaron personas.")

    def _format_details(self, detection):
        if not detection:
            return "No hay una persona seleccionada."
        names = (
            "Nariz", "Ojo izq. interior", "Ojo izq.", "Ojo izq. exterior",
            "Ojo der. interior", "Ojo der.", "Ojo der. exterior", "Oreja izq.",
            "Oreja der.", "Boca izq.", "Boca der.", "Hombro izq.", "Hombro der.",
            "Codo izq.", "Codo der.", "Muñeca izq.", "Muñeca der.", "Meñique izq.",
            "Meñique der.", "Índice izq.", "Índice der.", "Pulgar izq.", "Pulgar der.",
            "Cadera izq.", "Cadera der.", "Rodilla izq.", "Rodilla der.",
            "Tobillo izq.", "Tobillo der.", "Talón izq.", "Talón der.",
            "Pie izq.", "Pie der.",
        )
        lines = [
            "ID temporal: {}".format(detection["track_id"]),
            "Puntos visibles: {}/33".format(detection.get("visible_landmarks", 0)),
            "Visibilidad media: {:.1f}%".format(detection.get("mean_visibility", 0.0) * 100),
            "Caja: {}".format(detection["bbox"]),
            "",
            "PUNTOS (x%, y%, vis.):",
        ]
        for index, point in enumerate(detection["landmarks"]):
            x, y, _z, visibility = point
            if visibility >= 0.25:
                lines.append("{}: {:.1f}, {:.1f} ({:.0f}%)".format(
                    names[index] if index < len(names) else "Punto {}".format(index),
                    x * 100, y * 100, visibility * 100,
                ))
        return "\n".join(lines)

    def _set_details(self, value):
        if not hasattr(self, "details"):
            return
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", value)
        self.details.configure(state="disabled")

    def _draw_detections(self, frame, detections):
        from .vision import POSE_CONNECTIONS
        height, width = frame.shape[:2]
        for detection in detections:
            selected = detection["track_id"] == self.selected_track
            color = (50, 220, 80) if selected else (0, 210, 255)
            landmarks = detection["landmarks"]
            if self.show_skeleton.get():
                for start, end in POSE_CONNECTIONS:
                    if start >= len(landmarks) or end >= len(landmarks):
                        continue
                    a, b = landmarks[start], landmarks[end]
                    if a[3] >= 0.25 and b[3] >= 0.25:
                        p1 = (int(a[0] * width), int(a[1] * height))
                        p2 = (int(b[0] * width), int(b[1] * height))
                        self.cv2.line(frame, p1, p2, color, 3 if selected else 2, self.cv2.LINE_AA)
                for x, y, _z, visibility in landmarks:
                    if visibility >= 0.25:
                        self.cv2.circle(frame, (int(x * width), int(y * height)), 4 if selected else 3, color, -1, self.cv2.LINE_AA)
            x1, y1, x2, y2 = detection["bbox"]
            self.cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3 if selected else 2)
            label = "OBJETIVO" if selected else "Persona {}".format(detection["track_id"])
            self.cv2.putText(frame, label, (x1, max(22, y1 - 8)), self.cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

    def _render_still(self):
        if self.still_frame is None:
            return
        frame = self.still_frame.copy()
        self._draw_detections(frame, self.still_detections)
        self._show_frame(frame)
        selected = next((d for d in self.still_detections if d["track_id"] == self.selected_track), None)
        self._set_details(self._format_details(selected))

    def _refresh_still(self):
        if self.still_frame is not None:
            self._render_still()

    def _tick(self):
        if not self.running or self.capture is None:
            return
        ok, frame = self.capture.read()
        if not ok:
            self.pause()
            self.status.set("Fin de vídeo o no se pudo leer el fotograma.")
            return
        self.frame_index += 1
        try:
            detections = self.detector.detect(frame, int(time.monotonic() * 1000))
        except Exception as exc:
            self.pause()
            messagebox.showerror("Detección", str(exc), parent=self.parent)
            return
        ids = [d["track_id"] for d in detections]
        if self.selected_track not in ids:
            self.selected_track = ids[0] if ids else None
        self._update_people(detections)
        self._draw_detections(frame, detections)
        self._show_frame(frame)
        self.status.set(
            "Fotograma {} · {} persona(s) · objetivo {}".format(
                self.frame_index, len(detections), self.selected_track or "ninguno"
            )
        )
        fps = self.capture.get(self.cv2.CAP_PROP_FPS)
        delay = max(1, int(1000 / fps)) if fps > 0 and self.source_path.get() else 15
        self.parent.after(delay, self._tick)

    def _show_frame(self, frame):
        from PIL import Image, ImageTk
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        image.thumbnail((900, 620))
        self.photo = ImageTk.PhotoImage(image)
        self.preview.configure(image=self.photo, text="")

    def close(self):
        self.stop()
