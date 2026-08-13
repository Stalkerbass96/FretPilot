"""Canonical FretPilot Guitar IR."""

from fretpilot.ir.builder import build_guitar_ir
from fretpilot.ir.models import GuitarProjectIR, IRKnowledgeReference, SCHEMA_VERSION

__all__ = [
    "GuitarProjectIR",
    "IRKnowledgeReference",
    "SCHEMA_VERSION",
    "build_guitar_ir",
]
