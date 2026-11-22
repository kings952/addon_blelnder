"""Unified desktop tester for Genesis Mocap phases 1 and 2."""
import json, os, threading, tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .runner import BlendInspectionError, BlendInspector

class BlendInspectorWindow:
    def __init__(self, root):
        self.root = root
        root.title("Genesis Mocap - Tester integral")
        root.geometry("1180x780"); root.minsize(900, 650)
        self.inspection = None; self._busy = False; self.armature_by_label = {}
        self.blend_path = tk.StringVar(); self.blender_path = tk.StringVar(value=os.environ.get("BLENDER_EXECUTABLE", ""))
        self.selected_armature = tk.StringVar(); self.status = tk.StringVar(value="Selecciona un archivo .blend.")
        self.vision_panel = None; self._build()

    def _build(self):
        notebook = ttk.Notebook(self.root); notebook.pack(fill="both", expand=True)
        tab1, tab2 = ttk.Frame(notebook), ttk.Frame(notebook)
        notebook.add(tab1, text="Fase 1 · Inspector de rigs")
        notebook.add(tab2, text="Fase 2 · Motor de visión")
        outer = ttk.Frame(tab1, padding=12); outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Pruebas externas de armatures", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Analiza el .blend con Blender en segundo plano. No modifica el archivo original.").pack(anchor="w", pady=8)
        for label, var, command in (("Archivo .blend", self.blend_path, self._choose_blend), ("Ejecutable Blender", self.blender_path, self._choose_blender)):
            row = ttk.Frame(outer); row.pack(fill="x", pady=3)
            ttk.Label(row, text=label, width=18).pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True, padx=5)
            ttk.Button(row, text="Examinar...", command=command).pack(side="left")
        actions = ttk.Frame(outer); actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Detectar armatures", command=self._inspect).pack(side="left")
        ttk.Label(actions, textvariable=self.status).pack(side="left", padx=12)
        selector = ttk.LabelFrame(outer, text="Armatures encontrados", padding=8); selector.pack(fill="x", pady=6)
        self.combo = ttk.Combobox(selector, textvariable=self.selected_armature, state="readonly")
        self.combo.pack(side="left", fill="x", expand=True, padx=(0, 8)); self.combo.bind("<<ComboboxSelected>>", self._show_armature)
        ttk.Button(selector, text="Validar seleccionado", command=self._validate).pack(side="left")
        panel = ttk.LabelFrame(outer, text="Información y resultado", padding=8); panel.pack(fill="both", expand=True, pady=6)
        self.output = tk.Text(panel, wrap="none", font=("Consolas", 9), state="disabled")
        sy = ttk.Scrollbar(panel, orient="vertical", command=self.output.yview)
        sx = ttk.Scrollbar(panel, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.output.grid(row=0, column=0, sticky="nsew"); sy.grid(row=0, column=1, sticky="ns"); sx.grid(row=1, column=0, sticky="ew")
        panel.rowconfigure(0, weight=1); panel.columnconfigure(0, weight=1)
        try:
            from .vision_panel import VisionCapturePanel
            self.vision_panel = VisionCapturePanel(tab2)
        except ImportError as exc:
            ttk.Label(tab2, text="Dependencias de visión faltantes. Ejecuta pip install -r requirements.txt.\n{}".format(exc), padding=20).pack(anchor="w")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        if self.vision_panel: self.vision_panel.close()
        self.root.destroy()

    def _choose_blend(self):
        p = filedialog.askopenfilename(parent=self.root, filetypes=[("Blender", "*.blend")])
        if p: self.blend_path.set(p)

    def _choose_blender(self):
        p = filedialog.askopenfilename(parent=self.root, filetypes=[("Blender", "blender.exe"), ("Ejecutables", "*.exe"), ("Todos", "*.*")])
        if p: self.blender_path.set(p)

    def _set_output(self, value):
        self.output.configure(state="normal"); self.output.delete("1.0", "end")
        self.output.insert("1.0", value); self.output.configure(state="disabled")

    def _inspector(self): return BlendInspector(self.blender_path.get().strip() or None)

    def _inspect(self):
        if self._busy: return
        path = self.blend_path.get().strip()
        if not path:
            messagebox.showwarning("Falta el archivo", "Selecciona un archivo .blend.", parent=self.root); return
        self._busy = True; self.status.set("Analizando en Blender background...")
        threading.Thread(target=self._inspect_background, args=(path,), daemon=True).start()

    def _inspect_background(self, path):
        try: result, error = self._inspector().inspect(path), None
        except BlendInspectionError as exc: result, error = None, str(exc)
        self.root.after(0, self._finish_inspection, result, error)

    def _finish_inspection(self, result, error):
        self._busy = False
        if error:
            self.status.set("Error de inspección"); messagebox.showerror("No se pudo inspeccionar", error, parent=self.root); return
        self.inspection = result; self.armature_by_label.clear(); labels = []
        for item in result["armatures"]:
            label = "{} | {} huesos | {}".format(item["name"], item["bone_count"], item["data_name"])
            labels.append(label); self.armature_by_label[label] = item["name"]
        self.combo["values"] = labels
        if labels:
            self.combo.current(0); self.status.set("{} armature(s) detectado(s)".format(len(labels))); self._show_armature()
        else:
            self.selected_armature.set(""); self.status.set("No se encontraron armatures")
            self._set_output("No hay objetos ARMATURE.\nObjetos totales: {}".format(result["object_count"]))

    def _current_armature(self): return self.armature_by_label.get(self.selected_armature.get())

    def _show_armature(self, _event=None):
        name = self._current_armature()
        if name and self.inspection:
            item = next(x for x in self.inspection["armatures"] if x["name"] == name)
            self._set_output(json.dumps(item, ensure_ascii=False, indent=2))

    def _validate(self):
        name = self._current_armature()
        if not name or not self.inspection:
            messagebox.showwarning("Selecciona un armature", "Detecta el archivo y elige un armature.", parent=self.root); return
        try: report = self._inspector().validate_armature(self.inspection, name)
        except BlendInspectionError as exc:
            messagebox.showerror("Error de validación", str(exc), parent=self.root); return
        lines = ["ARMATURE: {}".format(report["armature_name"]), "Huesos del rig: {}".format(report["bone_count"]),
            "Perfil Genesis: {}/{} ({:.2f}%)".format(report["found_count"], report["required_bones"], report["percentage"]),
            "Destinos: {}".format(report["total_targets"]), "Estado: {}".format("VÁLIDO" if report["is_valid"] else "INCOMPLETO"), "", "HUESOS FALTANTES:"]
        lines.extend("  - " + x for x in (report["missing_bones"] or ["Ninguno"]))
        lines.extend(["", "CONTROLES AUXILIARES:"]); lines.extend("  - " + x for x in report["auxiliary_targets"])
        self._set_output("\n".join(lines)); self.status.set("Validación terminada")

def main():
    root = tk.Tk(); BlendInspectorWindow(root); root.mainloop()

if __name__ == "__main__": main()
