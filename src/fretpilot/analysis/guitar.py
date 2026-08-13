"""High-level guitar analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from fretpilot.articulation import ArticulationPlan, plan_articulations
from fretpilot.guitar import FingeringResult, optimize_fingering
from fretpilot.midi.models import NormalizedTrack
from fretpilot.rhythm import RhythmAnalysis, analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.knowledge.playing_contexts import PlayingContext


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
    string/fret candidates, while articulation preferences confidence-weight
    only techniques that pass deterministic eligibility rules.
    """

    rhythm = analyze_track_rhythm(track)
    fingering = optimize_fingering(
        track,
        max_fret=max_fret,
        preferences=playing_context.fingering if playing_context is not None else None,
    )
    articulations = plan_articulations(
        track,
        fingering,
        preferences=(
            playing_context.articulation if playing_context is not None else None
        ),
    )

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
        playing_context=playing_context,
    )
