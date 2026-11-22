"""Camera/video preview and visual target selector."""
import time, tkinter as tk
from tkinter import filedialog, messagebox, ttk

class VisionCapturePanel:
    def __init__(self, parent):
        import cv2
        from PIL import Image, ImageTk
        self.cv2 = cv2; self.parent = parent; self.capture = None; self.detector = None
        self.running = False; self.frame_index = 0; self.selected_track = None; self.photo = None
        self.source_path = tk.StringVar(); self.camera_index = tk.StringVar(value="0")
        self.model_path = tk.StringVar(); self.max_people = tk.IntVar(value=8)
        self.status = tk.StringVar(value="Abre un vídeo o conecta una cámara.")
        self._build()

    def _build(self):
        outer = ttk.Frame(self.parent, padding=10); outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Fase 2 · Motor de Visión", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Detección multi-persona. Los IDs son seguimientos temporales, no reconocimiento de identidad.", wraplength=1000).pack(anchor="w", pady=5)
        source = ttk.LabelFrame(outer, text="Fuente de captura", padding=8); source.pack(fill="x")
        row = ttk.Frame(source); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Vídeo", width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.source_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="Abrir vídeo...", command=self._choose_video).pack(side="left")
        row = ttk.Frame(source); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Cámara (índice)", width=18).pack(side="left")
        ttk.Entry(row, textvariable=self.camera_index, width=8).pack(side="left", padx=4)
        ttk.Button(row, text="Conectar cámara", command=self.open_camera).pack(side="left")
        ttk.Label(row, text="Máx. personas").pack(side="left", padx=(18, 4))
        ttk.Spinbox(row, from_=1, to=20, textvariable=self.max_people, width=5).pack(side="left")
        row = ttk.Frame(source); row.pack(fill="x", pady=2)
        ttk.Label(row, text="Modelo .task (opcional)", width=22).pack(side="left")
        ttk.Entry(row, textvariable=self.model_path).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Button(row, text="Buscar...", command=self._choose_model).pack(side="left")
        actions = ttk.Frame(outer); actions.pack(fill="x", pady=7)
        ttk.Button(actions, text="Iniciar / Reanudar", command=self.start).pack(side="left")
        ttk.Button(actions, text="Pausar", command=self.pause).pack(side="left", padx=5)
        ttk.Button(actions, text="Detener y liberar", command=self.stop).pack(side="left")
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=12)
        body = ttk.Frame(outer); body.pack(fill="both", expand=True)
        preview = ttk.LabelFrame(body, text="Vista de detección", padding=5); preview.pack(side="left", fill="both", expand=True)
        self.preview = ttk.Label(preview, text="La vista de cámara/vídeo aparecerá aquí", anchor="center")
        self.preview.pack(fill="both", expand=True)
        side = ttk.LabelFrame(body, text="Personas detectadas", padding=8); side.pack(side="right", fill="y", padx=(8, 0))
        ttk.Label(side, text="Sujeto objetivo:").pack(anchor="w")
        self.subject = ttk.Combobox(side, state="readonly", width=24); self.subject.pack(fill="x", pady=5)
        self.subject.bind("<<ComboboxSelected>>", self._select_subject)
        self.people_list = tk.Listbox(side, width=28, height=16); self.people_list.pack(fill="both", expand=True)
        self.people_list.bind("<<ListboxSelect>>", self._select_from_list)
        ttk.Label(side, text="Verde = objetivo\nAmarillo = otras personas").pack(anchor="w", pady=8)

    def _choose_video(self):
        path = filedialog.askopenfilename(parent=self.parent, filetypes=[("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"), ("Todos", "*.*")])
        if path: self.source_path.set(path); self.open_video(path)

    def _choose_model(self):
        path = filedialog.askopenfilename(parent=self.parent, filetypes=[("MediaPipe task", "*.task"), ("Todos", "*.*")])
        if path: self.model_path.set(path)

    def _release_capture(self):
        if self.capture is not None: self.capture.release(); self.capture = None

    def _prepare_detector(self):
        if self.detector is None:
            from .vision import MultiPersonPoseDetector
            self.status.set("Cargando modelo (la primera ejecución puede descargarlo)...")
            self.parent.update_idletasks()
            self.detector = MultiPersonPoseDetector(self.model_path.get().strip() or None, self.max_people.get())

    def open_video(self, path):
        self.stop(); cap = self.cv2.VideoCapture(path)
        if not cap.isOpened():
            cap.release(); messagebox.showerror("Vídeo", "No se pudo abrir el vídeo.", parent=self.parent); return
        self.capture = cap; self.frame_index = 0; self.status.set("Vídeo cargado. Pulsa Iniciar / Reanudar.")

    def open_camera(self):
        self.stop()
        try: index = int(self.camera_index.get())
        except ValueError:
            messagebox.showerror("Cámara", "El índice debe ser un número entero.", parent=self.parent); return
        cap = self.cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release(); messagebox.showerror("Cámara", "No se pudo abrir la cámara {}. Revisa conexión y permisos.".format(index), parent=self.parent); return
        self.capture = cap; self.frame_index = 0; self.status.set("Cámara conectada. Pulsa Iniciar / Reanudar.")

    def start(self):
        if self.capture is None:
            messagebox.showwarning("Sin fuente", "Abre un vídeo o conecta una cámara primero.", parent=self.parent); return
        try: self._prepare_detector()
        except Exception as exc:
            messagebox.showerror("Motor de visión", str(exc), parent=self.parent); self.status.set("No se pudo iniciar el detector."); return
        if not self.running: self.running = True; self.status.set("Procesando captura..."); self._tick()

    def pause(self):
        self.running = False
        if self.capture is not None: self.status.set("Captura pausada.")

    def stop(self):
        self.running = False; self._release_capture()
        if self.detector is not None: self.detector.close(); self.detector = None
        self.selected_track = None
        if hasattr(self, "subject"):
            self.subject["values"] = []; self.subject.set(""); self.people_list.delete(0, "end")
        if hasattr(self, "preview"): self.preview.configure(image="", text="La vista de cámara/vídeo aparecerá aquí"); self.photo = None
        if hasattr(self, "status"): self.status.set("Captura detenida y recursos liberados.")

    def _select_subject(self, _event=None):
        try: self.selected_track = int(self.subject.get().split("·")[0].replace("Persona", "").strip())
        except (ValueError, IndexError): self.selected_track = None

    def _select_from_list(self, _event=None):
        selection = self.people_list.curselection()
        if selection:
            labels = list(self.subject["values"])
            if selection[0] < len(labels): self.subject.current(selection[0]); self._select_subject()

    def _tick(self):
        if not self.running or self.capture is None: return
        ok, frame = self.capture.read()
        if not ok: self.pause(); self.status.set("Fin de vídeo o no se pudo leer el fotograma."); return
        self.frame_index += 1
        try: detections = self.detector.detect(frame, int(time.monotonic()*1000))
        except Exception as exc:
            self.pause(); messagebox.showerror("Detección", str(exc), parent=self.parent); return
        ids = [d["track_id"] for d in detections]
        if self.selected_track not in ids: self.selected_track = ids[0] if ids else None
        labels = ["Persona {} · {} puntos".format(d["track_id"], len(d["landmarks"])) for d in detections]
        self.subject["values"] = labels; self.people_list.delete(0, "end")
        for label in labels: self.people_list.insert("end", label)
        for i, d in enumerate(detections):
            if d["track_id"] == self.selected_track:
                self.subject.current(i); self.people_list.selection_clear(0, "end"); self.people_list.selection_set(i); break
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]; selected = d["track_id"] == self.selected_track
            color = (50, 220, 80) if selected else (0, 210, 255)
            self.cv2.rectangle(frame, (x1,y1), (x2,y2), color, 3 if selected else 2)
            self.cv2.putText(frame, "OBJETIVO" if selected else "Persona {}".format(d["track_id"]),
                (x1, max(22,y1-8)), self.cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
        self._show_frame(frame)
        self.status.set("Fotograma {} · {} persona(s) · objetivo {}".format(self.frame_index, len(detections), self.selected_track or "ninguno"))
        fps = self.capture.get(self.cv2.CAP_PROP_FPS)
        delay = max(1, int(1000/fps)) if fps > 0 and self.source_path.get() else 15
        self.parent.after(delay, self._tick)

    def _show_frame(self, frame):
        from PIL import Image, ImageTk
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb); image.thumbnail((900, 620))
        self.photo = ImageTk.PhotoImage(image); self.preview.configure(image=self.photo, text="")

    def close(self): self.stop()
