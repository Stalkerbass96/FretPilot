"""High-level musical analysis pipelines."""

from fretpilot.analysis.guitar import GuitarTrackAnalysis, analyze_guitar_track
from fretpilot.analysis.section_execution import (
    analyze_guitar_stream_section_aware as _base_stream,
    analyze_guitar_track_by_sections as _base_sections,
)
from fretpilot.analysis.section_contexts import (
    SectionContextAnalysis,
    analyze_section_contexts,
)
from fretpilot.analysis.sections import (
    GuitarSection,
    SectionSegmentation,
    segment_instrument_stream,
)
from fretpilot.articulation.models import ArticulationDecision
from fretpilot.guitar.fretting_digits import assign_fretting_digits
from fretpilot.midi.pitch_wheel import extract_monophonic_pitch_raises
from fretpilot.picking.sections import plan_picking_by_sections


def analyze_guitar_track_by_sections(track, section_contexts, **kwargs):
    result = _base_sections(track, section_contexts, **kwargs)
    result.fingering = assign_fretting_digits(track, result.fingering)
    result.picking = plan_picking_by_sections(
        track,
        result.fingering,
        result.section_contexts,
        kwargs.get("context_overrides"),
    )
    return result


def analyze_guitar_stream_section_aware(timeline, stream, **kwargs):
    track = stream.as_track()
    result = _base_stream(timeline, stream, **kwargs)
    result.fingering = assign_fretting_digits(track, result.fingering)
    result.picking = plan_picking_by_sections(
        track,
        result.fingering,
        result.section_contexts,
        kwargs.get("context_overrides"),
    )
    for gesture in extract_monophonic_pitch_raises(timeline, stream):
        semitones = float(gesture["semitones"])
        result.articulations.decisions.append(
            ArticulationDecision(
                note_index=int(gesture["note_index"]),
                technique="pitch_raise",
                confidence=0.94 if gesture["returned_to_center"] else 0.86,
                reason=(
                    f"Explicit wheel gesture raises pitch by about {semitones:.2f} semitones "
                    "with a declared range on a monophonic stream."
                ),
                parameters={
                    "semitones": semitones,
                    "peak_wheel": float(gesture["peak_wheel"]),
                    "range_semitones": float(gesture["range_semitones"]),
                },
            )
        )
    result.articulations.decisions.sort(
        key=lambda item: (
            item.note_index,
            item.source_note_index if item.source_note_index is not None else -1,
            item.technique,
        )
    )
    return result


__all__ = [
    "GuitarSection",
    "GuitarTrackAnalysis",
    "SectionContextAnalysis",
    "SectionSegmentation",
    "analyze_guitar_stream_section_aware",
    "analyze_guitar_track",
    "analyze_guitar_track_by_sections",
    "analyze_section_contexts",
    "segment_instrument_stream",
]
