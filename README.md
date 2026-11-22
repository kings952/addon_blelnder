# addon_blelnder

Addon y herramientas de diagnóstico para rigs Genesis 4C en Blender 5.x.

## Addon — Fase 1

La extensión `app/genesis_mocap` incorpora el panel **Genesis Mocap** en la Vista 3D, selector de Armature y validación del perfil de 58 destinos: 52 huesos Genesis requeridos y 6 controles auxiliares sin hueso fuente directo.

## Inspector externo de archivos .blend (sin instalar el addon)

La aplicación `app/genesis_mocap_tester` permite probar rigs antes de instalar o activar la extensión:

1. Abre una ventana para seleccionar un archivo .blend.
2. Ejecuta Blender en modo `--background`, sin abrir su interfaz.
3. Detecta todos los objetos ARMATURE.
4. Muestra nombre, datablock, cantidad de huesos, jerarquía padre, `use_deform`, coordenadas locales de cabeza/cola y longitud.
5. Permite elegir un Armature y validar el perfil Genesis, mostrando huesos encontrados y faltantes.
6. No guarda ni modifica el archivo original y no necesita instalar el addon.

### Requisitos

- Python 3.10+ con Tkinter.
- Blender 5.x instalado (no se instala en el entorno virtual).
- No requiere `bpy`, `mathutils`, cámara ni MediaPipe.

### Ejecutar en Windows PowerShell

Desde la raíz del repositorio:

```powershell
# Opcional: si Blender no está en PATH, indica la ruta real:
$env:BLENDER_EXECUTABLE = "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
$env:PYTHONPATH = "app"
python -m genesis_mocap_tester
```

También puedes seleccionar `blender.exe` desde la ventana. Elige el .blend, pulsa **Detectar armatures**, selecciona el rig y pulsa **Validar seleccionado**.

El inspector usa un proceso Blender independiente en segundo plano. No guarda el proyecto. Si Blender no puede abrir el archivo, la ventana presenta el error y el log disponible.

## Pruebas automatizadas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

Las pruebas simulan el proceso de Blender para comprobar ejecución, lectura del informe, selección/validación, rutas inválidas, timeout y archivos sin armatures. Se ejecutan sin abrir Blender. La lectura real de un .blend se verifica al ejecutar el inspector: la simulación no sustituye esa prueba de integración.

## Estructura

```text
app/
  genesis_mocap/              # Addon instalable
  genesis_mocap_tester/       # Inspector externo de .blend
    blender_worker.py         # Script dentro de Blender background
    runner.py                 # Ejecuta Blender y procesa JSON
    gui.py                    # Ventana de selección y validación
    __main__.py
tests/                        # Pruebas automatizadas fuera de app/
```

## Compatibilidad de iconos

`ORIENTATION` no es un identificador válido en Blender 5.3. Si aparece en una copia externa/antigua del addon, reemplázalo por `ORIENTATION_GIMBAL` o elimina el argumento `icon`. El traceback recibido apunta a `genesis_mocap_bridge.py`, archivo que no existe en esta rama; el addon del repositorio usa iconos válidos como `ARMATURE_DATA`, `INFO`, `ERROR` y `CHECKMARK`. Para corregir ese archivo externo de forma permanente hay que incorporar su fuente al repositorio.

## Fuera del alcance de Fase 1

Captura de cámara/vídeo, MediaPipe, seguimiento multi-sujeto, solver, retargeting, filtros de oclusión y optimización de keyframes quedan para fases posteriores. La validación no modifica el rig ni crea keyframes.
