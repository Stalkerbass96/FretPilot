"""High-level guitar analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from fretpilot.articulation import ArticulationPlan, plan_articulations
from fretpilot.guitar import FingeringResult, optimize_fingering
from fretpilot.knowledge import PlayingContext
from fretpilot.midi.models import NormalizedTrack
from fretpilot.rhythm import RhythmAnalysis, analyze_track_rhythm


@dataclass(slots=True)
class GuitarTrackAnalysis:
    track_index: int
    track_name: str
    rhythm: RhythmAnalysis
    fingering: FingeringResult
    articulations: ArticulationPlan
    playing_context: PlayingContext | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def analyze_guitar_track(
    track: NormalizedTrack,
    *,
    max_fret: int = 24,
    playing_context: PlayingContext | None = None,
) -> GuitarTrackAnalysis:
    """Run the deterministic FretPilot intelligence stack on a guitar track.

    ``playing_context`` is optional so existing callers remain backward-
    compatible. When supplied, its fingering preferences rank physically valid
    string/fret candidates. Articulation context is intentionally left for
    GK-004 so this change does not silently alter technique inference yet.
    """

    rhythm = analyze_track_rhythm(track)
    fingering = optimize_fingering(
        track,
        max_fret=max_fret,
        preferences=playing_context.fingering if playing_context is not None else None,
    )
    articulations = plan_articulations(track, fingering)

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
        playing_context=playing_context,
    )
