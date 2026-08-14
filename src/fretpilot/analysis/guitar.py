"""High-level guitar analysis pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import TYPE_CHECKING, Any

from fretpilot.articulation import ArticulationPlan, plan_articulations
from fretpilot.guitar import FingeringResult, optimize_fingering
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.harmony import HarmonyPlan, plan_harmony
from fretpilot.midi.models import NormalizedTrack
from fretpilot.picking import PickingPlan, plan_picking
from fretpilot.rhythm import RhythmAnalysis, analyze_track_rhythm

if TYPE_CHECKING:
    from fretpilot.analysis.section_contexts import SectionContextAnalysis
    from fretpilot.guitar.hand_position import HandPositionState
    from fretpilot.knowledge.playing_contexts import PlayingContext


@dataclass(slots=True)
class GuitarTrackAnalysis:
    track_index: int
    track_name: str
    rhythm: RhythmAnalysis
    fingering: FingeringResult
    articulations: ArticulationPlan
    picking: PickingPlan | None = None
    harmony: HarmonyPlan | None = None
    playing_context: PlayingContext | None = None
    section_contexts: list[SectionContextAnalysis] = field(default_factory=list)
    hand_positions: list[HandPositionState] = field(default_factory=list)

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
    """Run one-context deterministic guitar analysis."""

    rhythm = analyze_track_rhythm(track)
    fingering_track = align_track_onsets_to_rhythm(track, rhythm)
    fingering = optimize_fingering(
        fingering_track,
        max_fret=max_fret,
        preferences=playing_context.fingering if playing_context is not None else None,
    )
    fingering = assign_fretting_digits(track, fingering)
    articulations = plan_articulations(
        track,
        fingering,
        preferences=(
            playing_context.articulation if playing_context is not None else None
        ),
    )
    picking = plan_picking(track, fingering, context=playing_context)
    harmony = plan_harmony(track, fingering)

    return GuitarTrackAnalysis(
        track_index=track.index,
        track_name=track.name,
        rhythm=rhythm,
        fingering=fingering,
        articulations=articulations,
        picking=picking,
        harmony=harmony,
        playing_context=playing_context,
    )
