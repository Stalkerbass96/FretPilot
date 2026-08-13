"""Guitar instrument intelligence."""

from fretpilot.guitar.fingering import optimize_fingering
from fretpilot.guitar.instrument import STANDARD_TUNING, candidate_positions
from fretpilot.guitar.models import (
    FingeringResult,
    FretPosition,
    HandPositionPlan,
    HandPositionState,
    HandPositionTransition,
    SectionHandPosition,
)

__all__ = [
    "FingeringResult",
    "FretPosition",
    "HandPositionPlan",
    "HandPositionState",
    "HandPositionTransition",
    "SectionHandPosition",
    "STANDARD_TUNING",
    "candidate_positions",
    "optimize_fingering",
]
