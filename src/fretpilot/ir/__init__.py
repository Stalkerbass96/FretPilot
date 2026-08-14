"""Canonical FretPilot Guitar IR."""

from fretpilot.ir.models import GuitarProjectIR, IRKnowledgeReference, SCHEMA_VERSION
from fretpilot.ir.project_builder import build_guitar_ir

__all__ = [
    "GuitarProjectIR",
    "IRKnowledgeReference",
    "SCHEMA_VERSION",
    "build_guitar_ir",
]
