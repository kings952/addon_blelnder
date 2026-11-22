# addon_blelnder

Addon de Blender dedicado a Genesis 4C.

## Fase 1 — Base y UI

La extensión inicial para Blender 5.X incorpora:
- Panel **Genesis Mocap** en la barra lateral de la Vista 3D.
- Selector de un objeto Armature.
- Validación de los 58 destinos del perfil Genesis definido en el TDD.
- Pruebas automatizadas independientes de Blender.

### Estructura

```text
app/
  genesis_mocap/
    blender_manifest.toml
    __init__.py
    core/
    operators/
    ui/
tests/
  test_bone_mapping.py
  test_armature_validator.py
  test_addon_structure.py
```

### Ejecutar pruebas

Desde la raíz del repositorio, con el entorno virtual activo:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas no necesitan Blender, cámara ni modelos externos.

### Instalar y probar en Blender 5.X

Instala la extensión desde la carpeta `app/genesis_mocap`, conservando `blender_manifest.toml` en la raíz del paquete. Habilítala y abre **3D View > Sidebar (N) > Genesis Mocap**. Selecciona el Armature Genesis y pulsa **Validar huesos Genesis**.

El perfil contiene 58 destinos: 52 nombres de huesos Genesis requeridos y 6 controles auxiliares sin hueso fuente directo (Bend Goals y ojos). La validación no modifica el rig ni crea keyframes.

La captura de cámara, MediaPipe, seguimiento multi-sujeto, solver, retargeting y optimización de keyframes pertenecen a fases posteriores.
