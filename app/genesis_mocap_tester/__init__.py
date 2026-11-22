"""Standalone .blend inspector; it does not require installing the add-on."""
from .runner import BlendInspector, BlendInspectionError

__all__ = ["BlendInspector", "BlendInspectionError"]
