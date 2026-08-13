"""High-level guitar analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING, Any

from fretpilot.articulation import ArticulationPlan, plan_articulations
from fretpilot.guitar import FingeringResult, optimize_fingering
from fretpilot.midi.models import NormalizedTrack
from fretpilot.rhythm import RhythmAnalysis, analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.analysis.section_contexts import SectionContextAnalysis
    from fretpilot.guitar.models import HandPositionPlan
    from fretpilot.knowledge.playing_contexts import PlayingContext


@dataclass(slots=True)
class GuitarTrackAnalysis:
    track_index: int
    track_name: str
    rhythm: RhythmAnalysis
    fingering: FingeringResult
    articulations: ArticulationPlan
    playing_context: PlayingContext | None = None
    # A section-aware analysis keeps time-varying musical contexts here.  The
    # legacy/single-context path leaves the list empty, preserving compatibility.
    section_contexts: list[SectionContextAnalysis] = field(default_factory=list)
    hand_position_plan: HandPositionPlan | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def align_track_onsets_to_rhythm(
    track: NormalizedTrack,
    rhythm: RhythmAnalysis,
) -> NormalizedTrack:
    """Expose score-simultaneous notes to hard chord-fingering constraints.

    Humanized MIDI attacks often have slightly different source ticks but snap
    to the same notation onset. Only the working ``start_tick`` is aligned;
    original beat/tick timing remains on the source track and later in Guitar
    IR performance timing.
    """

    targets = {item.note_index: item.target_start_beat for item in rhythm.suggestions}
    if len(targets) != len(track.notes):
        raise ValueError("Rhythm suggestions must cover every track note.")
    return NormalizedTrack(
        index=track.index,
        name=track.name,
        notes=[
            replace(note, start_tick=round(targets[index] * 1_000_000))
            for index, note in enumerate(track.notes)
        ],
        instrument_name=track.instrument_name,
    )


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

    This function intentionally represents one context across the whole track.
    Use ``analyze_guitar_stream_section_aware`` when a stream may change role or
    style over time.
    """

    rhythm = analyze_track_rhythm(track)
    fingering_track = align_track_onsets_to_rhythm(track, rhythm)
    fingering = optimize_fingering(
        fingering_track,
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
