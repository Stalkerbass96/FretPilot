"""High-level guitar analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fretpilot.articulation import ArticulationPlan, plan_articulations
from fretpilot.guitar import FingeringResult, optimize_fingering
from fretpilot.midi.models import NormalizedTrack
from fretpilot.rhythm import RhythmAnalysis, analyze_track_rhythm


@dataclass(slots=True)
class GuitarTrackAnalysis:
    track_index: int
    track_name: str
    rhythm: RhythmAnalysis
    fingering: FingeringResult
    articulations: ArticulationPlan

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_guitar_track(
    track: NormalizedTrack,
    *,
    max_fret: int = 24,
) -> GuitarTrackAnalysis:
    """Run the current deterministic FretPilot intelligence stack on a track."""

    rhythm = analyze_track_rhythm(track)
    fingering = optimize_fingering(track, max_fret=max_fret)
    articulations = plan_articulations(track, fingering)

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
    )
