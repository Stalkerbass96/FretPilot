"""Render canonical Guitar IR as a review-friendly PDF TAB score.

The PDF output is intentionally independent of Guitar Pro. V0.1 renders six-line
TAB, measure positions, exact duration labels, ties, generic guitar techniques,
canonical harmony labels, explicit rest spans, and deterministic per-voice
rhythmic stem/beam lanes with dotted and tuplet marks. It is designed for
review and prototype validation rather than final publishing.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from fretpilot.exporters.pdf_score.rhythm import (
    measure_beam_segments,
    measure_notated_rests,
    measure_rhythm_onsets,
    measure_tuplet_groups,
)
from fretpilot.ir.models import (
    GuitarMeasure,
    GuitarNoteEvent,
    GuitarProjectIR,
    GuitarTrackIR,
)


@dataclass(slots=True)
class PDFScoreExportResult:
    path: str
    page_count: int
    track_count: int
    measure_count: int
    note_count: int
    maximum_voice_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "page_count": self.page_count,
            "track_count": self.track_count,
            "measure_count": self.measure_count,
            "note_count": self.note_count,
            "maximum_voice_count": self.maximum_voice_count,
            "warnings": self.warnings,
        }


@dataclass(frozen=True, slots=True)
class _TechniquePlacement:
    x: float
    text: str
    width: float


@dataclass(frozen=True, slots=True)
class _TechniqueDraw:
    x: float
    y: float
    text: str


def _layout_technique_labels(
    placements: list[_TechniquePlacement],
    *,
    base_y: float,
    lane_gap: float = 6.5,
    maximum_lanes: int = 2,
    horizontal_gap: float = 2.0,
) -> tuple[list[_TechniqueDraw], int]:
    """Place technique labels in deterministic lanes without overlap."""

    lane_ends = [float("-inf")] * maximum_lanes
    last_right_by_text: dict[str, float] = {}
    draws: list[_TechniqueDraw] = []
    condensed = 0
    for placement in sorted(placements, key=lambda item: (item.x, item.text)):
        left = placement.x - placement.width / 2
        right = placement.x + placement.width / 2
        if left <= last_right_by_text.get(
            placement.text,
            float("-inf"),
        ) + horizontal_gap:
            condensed += 1
            continue

        lane = next(
            (
                index
                for index, lane_end in enumerate(lane_ends)
                if left > lane_end + horizontal_gap
            ),
            None,
        )
        if lane is None:
            condensed += 1
            continue
        draws.append(
            _TechniqueDraw(
                x=placement.x,
                y=base_y + lane * lane_gap,
                text=placement.text,
            )
        )
        lane_ends[lane] = right
        last_right_by_text[placement.text] = right
    return draws, condensed


def _duration_label(beats: float) -> str:
    candidates = [
        (4.0, "1"),
        (3.0, "1/2."),
        (2.0, "1/2"),
        (1.5, "1/4."),
        (4 / 3, "1/2T"),
        (1.0, "1/4"),
        (0.75, "1/8."),
        (2 / 3, "4T"),
        (0.5, "1/8"),
        (0.375, "1/16."),
        (1 / 3, "8T"),
        (0.25, "1/16"),
        (0.1875, "1/32."),
        (1 / 6, "16T"),
        (0.125, "1/32"),
    ]
    value, label = min(candidates, key=lambda item: abs(item[0] - beats))
    if abs(value - beats) <= 1e-6:
        return label
    return f"{beats:.3g}b"


def _technique_label(event: GuitarNoteEvent) -> list[str]:
    mapping = {
        "hammer_on": "H",
        "pull_off": "P",
        "slide": "S",
        "legato_slide": "LS",
        "vibrato": "vib.",
        "let_ring": "let ring",
        "palm_mute": "P.M.",
        "natural_harmonic": "N.H.",
        "bend": "bend",
        "pitch_raise": "bend",
    }
    labels: list[str] = []
    for articulation in event.articulations:
        label = mapping.get(articulation.type, articulation.type.replace("_", " "))
        if label not in labels:
            labels.append(label)
    return labels


def _harmony_label_map(track: GuitarTrackIR) -> dict[float, str]:
    """Map canonical harmony regions to their first score-time anchor."""

    events = [
        event
        for measure in track.measures
        for event in measure.events
        if not event.score.tie_in
    ]
    labels: dict[float, str] = {}
    for region in track.harmony_regions:
        source_indices = set(region.source_note_indices)
        anchor = next(
            (
                event
                for event in events
                if event.source_note_index in source_indices
            ),
            None,
        )
        beat = anchor.score.start_beat if anchor is not None else region.start_beat
        labels.setdefault(round(beat, 7), region.symbol)
    return labels


def _time_x(
    measure_x: float,
    measure_width: float,
    measure: GuitarMeasure,
    absolute_beat: float,
) -> float:
    beat_in_measure = absolute_beat - measure.start_beat
    ratio = max(0.0, min(1.0, beat_in_measure / measure.duration_beats))
    return measure_x + 7 + (measure_width - 14) * ratio


def _measure_for_voice(measure: GuitarMeasure, voice: int) -> GuitarMeasure:
    """Return a score-layout view containing only one notation voice."""

    if voice not in {1, 2}:
        raise ValueError(f"PDF/TAB supports voices 1 and 2 only, not voice {voice}.")
    return GuitarMeasure(
        number=measure.number,
        start_beat=measure.start_beat,
        duration_beats=measure.duration_beats,
        numerator=measure.numerator,
        denominator=measure.denominator,
        events=[event for event in measure.events if event.score.voice == voice],
    )


def _measure_voices(measure: GuitarMeasure) -> list[int]:
    voices = sorted({event.score.voice for event in measure.events})
    unsupported = [voice for voice in voices if voice not in {1, 2}]
    if unsupported:
        raise ValueError(
            f"PDF/TAB supports voices 1 and 2 only; measure {measure.number} "
            f"uses {unsupported}."
        )
    return voices or [1]


def _system_uses_voice_two(measures: list[GuitarMeasure]) -> bool:
    return any(2 in _measure_voices(measure) for measure in measures)


def _maximum_voice_count(project: GuitarProjectIR) -> int:
    maximum = 1
    for track in project.tracks:
        for measure in track.measures:
            voices = _measure_voices(measure)
            maximum = max(maximum, *voices)
    return maximum


class _PDFScoreRenderer:
    def __init__(
        self,
        project: GuitarProjectIR,
        output: Path,
        *,
        measures_per_system: int,
        systems_per_page: int,
    ) -> None:
        self.project = project
        self.output = output
        self.measures_per_system = measures_per_system
        self.systems_per_page = systems_per_page
        self.page_size = landscape(A4)
        self.width, self.height = self.page_size
        self.canvas = canvas.Canvas(str(output), pagesize=self.page_size)
        self.page_count = 0
        self.margin_x = 42.0
        self.current_y = self.height - 55.0
        self.warnings: list[str] = []

    def _new_page(self, section: str) -> None:
        if self.page_count:
            self._draw_footer()
            self.canvas.showPage()
        self.page_count += 1
        self.current_y = self.height - 55.0
        self.canvas.setFillColor(colors.HexColor("#111827"))
        self.canvas.setFont("Helvetica-Bold", 10)
        self.canvas.drawString(self.margin_x, self.height - 24, self.project.title)
        self.canvas.setFont("Helvetica", 9)
        self.canvas.setFillColor(colors.HexColor("#4B5563"))
        self.canvas.drawRightString(self.width - self.margin_x, self.height - 24, section)
        self.canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.canvas.line(
            self.margin_x,
            self.height - 30,
            self.width - self.margin_x,
            self.height - 30,
        )

    def _draw_footer(self) -> None:
        self.canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.canvas.line(self.margin_x, 25, self.width - self.margin_x, 25)
        self.canvas.setFillColor(colors.HexColor("#6B7280"))
        self.canvas.setFont("Helvetica", 7.5)
        self.canvas.drawString(
            self.margin_x,
            13,
            "FretPilot PDF score - TAB review output",
        )
        self.canvas.drawRightString(
            self.width - self.margin_x,
            13,
            f"Page {self.page_count}",
        )

    def draw_cover(self) -> None:
        self._new_page("PDF score")
        y = self.height - 105
        self.canvas.setFillColor(colors.HexColor("#111827"))
        self.canvas.setFont("Helvetica-Bold", 26)
        self.canvas.drawString(self.margin_x, y, self.project.title or "Untitled")
        y -= 28
        self.canvas.setFont("Helvetica", 13)
        self.canvas.setFillColor(colors.HexColor("#374151"))
        self.canvas.drawString(self.margin_x, y, "FretPilot guitar score preview")
        y -= 38
        self.canvas.setFillColor(colors.HexColor("#F3F4F6"))
        self.canvas.roundRect(
            self.margin_x,
            y - 75,
            self.width - 2 * self.margin_x,
            75,
            8,
            fill=1,
            stroke=0,
        )
        self.canvas.setFillColor(colors.HexColor("#111827"))
        self.canvas.setFont("Helvetica-Bold", 10)
        self.canvas.drawString(self.margin_x + 18, y - 20, "Project summary")
        measure_count = sum(len(track.measures) for track in self.project.tracks)
        note_count = sum(
            len(measure.events)
            for track in self.project.tracks
            for measure in track.measures
        )
        tempo = self.project.tempo_map[0].bpm if self.project.tempo_map else 120.0
        self.canvas.setFont("Helvetica", 9)
        self.canvas.drawString(self.margin_x + 18, y - 39, f"Tempo: {tempo:.1f} BPM")
        self.canvas.drawString(
            self.margin_x + 160,
            y - 39,
            f"Tracks: {len(self.project.tracks)}",
        )
        self.canvas.drawString(
            self.margin_x + 270,
            y - 39,
            f"Measures: {measure_count}",
        )
        self.canvas.drawString(
            self.margin_x + 400,
            y - 39,
            f"Score events: {note_count}",
        )
        self.canvas.drawString(
            self.margin_x + 18,
            y - 57,
            f"Guitar IR schema: {self.project.schema_version} | Source: {Path(self.project.source).name}",
        )
        y -= 105
        self.canvas.setFont("Helvetica-Bold", 11)
        self.canvas.drawString(self.margin_x, y, "Notation legend")
        y -= 20
        self.canvas.setFont("Helvetica", 8.5)
        self.canvas.setFillColor(colors.HexColor("#374151"))
        legend = [
            "Chord symbols above TAB come from canonical Guitar IR harmony regions.",
            "R + duration marks explicit silent score spans, for example R 1/4.",
            "Stems, flags, beams, dots, and tuplet brackets below TAB show the written rhythmic skeleton.",
            "Two-voice TAB uses separate V1/V2 rhythm lanes; V1 stems descend and V2 stems ascend.",
            "Duration labels use exact written values; unsupported values show their beat length instead of being rounded.",
            "Technique labels: H hammer-on, P pull-off, S slide, LS legato slide, vib., let ring, P.M.",
            "Fret numbers are positioned on standard six-line TAB. Ties are drawn at measure boundaries.",
            "This V0.1 PDF is a review format; standard notation and advanced engraving remain future work.",
        ]
        for line in legend:
            self.canvas.drawString(self.margin_x, y, line)
            y -= 16

    def _draw_rhythm_lane(
        self,
        measure: GuitarMeasure,
        *,
        measure_x: float,
        measure_width: float,
        note_y: float,
        direction: int,
    ) -> None:
        """Draw the remote rhythm model for one isolated notation voice."""

        onsets = measure_rhythm_onsets(measure)
        beam_segments = measure_beam_segments(measure, onsets)
        tuplet_groups = measure_tuplet_groups(measure, onsets)
        onset_x = [
            _time_x(measure_x, measure_width, measure, onset.start_beat)
            for onset in onsets
        ]
        primary_beam_y = note_y + direction * 12.0
        covered_beams: set[tuple[int, int]] = set()
        for segment in beam_segments:
            for onset_index in range(segment.first_onset, segment.last_onset + 1):
                covered_beams.add((onset_index, segment.level))

        self.canvas.setStrokeColor(colors.HexColor("#374151"))
        for onset_index, onset in enumerate(onsets):
            if not onset.stemmed:
                continue
            stem_end_y = primary_beam_y + direction * max(
                0,
                onset.beam_level - 1,
            ) * 3.0
            self.canvas.setLineWidth(0.75)
            self.canvas.line(
                onset_x[onset_index],
                note_y,
                onset_x[onset_index],
                stem_end_y,
            )
            if onset.dot_count:
                self.canvas.setFillColor(colors.HexColor("#374151"))
                self.canvas.circle(
                    onset_x[onset_index] + 4.0,
                    note_y + 1.0,
                    0.95,
                    fill=1,
                    stroke=0,
                )

        for segment in beam_segments:
            beam_y = primary_beam_y + direction * (segment.level - 1) * 3.0
            self.canvas.setStrokeColor(colors.HexColor("#374151"))
            self.canvas.setLineWidth(1.45)
            self.canvas.line(
                onset_x[segment.first_onset],
                beam_y,
                onset_x[segment.last_onset],
                beam_y,
            )

        for onset_index, onset in enumerate(onsets):
            for level in range(1, onset.beam_level + 1):
                if (onset_index, level) in covered_beams:
                    continue
                flag_y = primary_beam_y + direction * (level - 1) * 3.0
                self.canvas.setStrokeColor(colors.HexColor("#374151"))
                self.canvas.setLineWidth(1.15)
                self.canvas.line(
                    onset_x[onset_index],
                    flag_y,
                    onset_x[onset_index] + 4.5,
                    flag_y + direction * 1.5,
                )

        for group in tuplet_groups:
            max_level = max(
                onsets[item].beam_level
                for item in range(group.first_onset, group.last_onset + 1)
            )
            bracket_y = primary_beam_y + direction * max(
                9.0,
                (max_level - 1) * 3.0 + 9.0,
            )
            left = onset_x[group.first_onset]
            right = onset_x[group.last_onset]
            middle = (left + right) / 2.0
            self.canvas.setStrokeColor(colors.HexColor("#4B5563"))
            self.canvas.setLineWidth(0.55)
            self.canvas.line(left, bracket_y, middle - 4.0, bracket_y)
            self.canvas.line(middle + 4.0, bracket_y, right, bracket_y)
            self.canvas.line(
                left,
                bracket_y,
                left,
                bracket_y - direction * 2.5,
            )
            self.canvas.line(
                right,
                bracket_y,
                right,
                bracket_y - direction * 2.5,
            )
            self.canvas.setFillColor(colors.HexColor("#374151"))
            self.canvas.setFont("Helvetica-Bold", 5.5)
            self.canvas.drawCentredString(
                middle,
                bracket_y + direction * 1.8,
                str(group.number),
            )

    def _draw_system(
        self,
        measures: list[GuitarMeasure],
        y: float,
        harmony_labels: dict[float, str],
    ) -> float:
        x0 = self.margin_x + 38
        x1 = self.width - self.margin_x
        measure_width = (x1 - x0) / self.measures_per_system
        line_gap = 8.2
        tab_top = y - 27
        tab_bottom = tab_top - 5 * line_gap
        has_voice_two = _system_uses_voice_two(measures)
        tuning_labels = {1: "e", 2: "B", 3: "G", 4: "D", 5: "A", 6: "E"}

        self.canvas.setFillColor(colors.HexColor("#111827"))
        self.canvas.setFont("Helvetica-Bold", 8)
        self.canvas.drawString(self.margin_x, tab_top - 18, "TAB")
        self.canvas.setFont("Helvetica", 6.5)
        self.canvas.setFillColor(colors.HexColor("#6B7280"))
        for string in range(1, 7):
            yy = tab_top - (string - 1) * line_gap
            self.canvas.drawRightString(x0 - 4, yy - 2.1, tuning_labels[string])

        self.canvas.setStrokeColor(colors.HexColor("#374151"))
        self.canvas.setLineWidth(0.45)
        for string in range(1, 7):
            yy = tab_top - (string - 1) * line_gap
            self.canvas.line(x0, yy, x1, yy)

        for index in range(self.measures_per_system):
            measure_x = x0 + index * measure_width
            measure = measures[index] if index < len(measures) else None
            self.canvas.setStrokeColor(colors.HexColor("#111827"))
            self.canvas.setLineWidth(0.8)
            self.canvas.line(measure_x, tab_top + 1, measure_x, tab_bottom - 1)
            if measure is None:
                continue

            self.canvas.setFillColor(colors.HexColor("#374151"))
            self.canvas.setFont("Helvetica-Bold", 7)
            self.canvas.drawString(measure_x + 3, tab_top + 10, str(measure.number))
            self.canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
            self.canvas.setLineWidth(0.25)
            for beat in range(1, measure.numerator):
                guide_x = measure_x + measure_width * (beat / measure.numerator)
                self.canvas.line(guide_x, tab_top + 2, guide_x, tab_bottom - 2)

            measure_end = measure.start_beat + measure.duration_beats
            for absolute_start, symbol in sorted(harmony_labels.items()):
                if not (
                    measure.start_beat - 1e-7
                    <= absolute_start
                    < measure_end - 1e-7
                ):
                    continue
                chord_x = _time_x(
                    measure_x,
                    measure_width,
                    measure,
                    absolute_start,
                )
                self.canvas.setFillColor(colors.HexColor("#111827"))
                self.canvas.setFont("Helvetica-Bold", 7.4)
                self.canvas.drawCentredString(chord_x, tab_top + 29, symbol)

            voices = _measure_voices(measure)
            voice_measures = {
                voice: _measure_for_voice(measure, voice)
                for voice in voices
            }
            for voice, voice_measure in voice_measures.items():
                label_y = tab_top + 2.5 if voice == 1 else tab_bottom - 5.5
                for rest in measure_notated_rests(voice_measure):
                    midpoint = rest.start_beat + rest.duration_beats / 2.0
                    rest_x = _time_x(
                        measure_x,
                        measure_width,
                        measure,
                        midpoint,
                    )
                    self.canvas.setFillColor(colors.HexColor("#6B7280"))
                    self.canvas.setFont("Helvetica-Oblique", 5.4)
                    prefix = f"V{voice} " if has_voice_two else ""
                    self.canvas.drawCentredString(
                        rest_x,
                        label_y,
                        f"{prefix}R {_duration_label(rest.duration_beats)}",
                    )

                self._draw_rhythm_lane(
                    voice_measure,
                    measure_x=measure_x,
                    measure_width=measure_width,
                    note_y=tab_bottom - (12 if voice == 1 else 55),
                    direction=-1 if voice == 1 else 1,
                )

            grouped: dict[tuple[int, float], list[GuitarNoteEvent]] = defaultdict(list)
            for event in measure.events:
                grouped[
                    (event.score.voice, round(event.score.start_beat, 7))
                ].append(event)

            technique_placements: list[_TechniquePlacement] = []
            for (voice, absolute_start), events in sorted(grouped.items()):
                note_x = _time_x(
                    measure_x,
                    measure_width,
                    measure,
                    absolute_start,
                )
                duration = min(event.score.duration_beats for event in events)
                self.canvas.setFillColor(colors.HexColor("#374151"))
                self.canvas.setFont("Helvetica", 5.8)
                duration_y = tab_top + 2.5 if voice == 1 else tab_bottom - 5.5
                prefix = f"V{voice} " if has_voice_two else ""
                self.canvas.drawCentredString(
                    note_x,
                    duration_y,
                    f"{prefix}{_duration_label(duration)}",
                )

                labels: list[str] = []
                for event in events:
                    for label in _technique_label(event):
                        if label not in labels:
                            labels.append(label)
                if labels:
                    text = ", ".join(labels[:3])
                    technique_placements.append(
                        _TechniquePlacement(
                            x=note_x,
                            text=text,
                            width=self.canvas.stringWidth(
                                text,
                                "Helvetica-Oblique",
                                5.4,
                            ),
                        )
                    )

                for event in events:
                    string = event.fingering.string
                    fret = event.fingering.fret
                    if string is None or fret is None or not 1 <= string <= 6:
                        string = 3
                        text = "?"
                        warning = f"Event {event.id} has no printable string/fret assignment."
                        if warning not in self.warnings:
                            self.warnings.append(warning)
                    else:
                        text = str(fret)
                    yy = tab_top - (string - 1) * line_gap
                    self.canvas.setFont("Helvetica-Bold", 7.4)
                    width = self.canvas.stringWidth(text, "Helvetica-Bold", 7.4)
                    self.canvas.setFillColor(colors.white)
                    self.canvas.rect(
                        note_x - width / 2 - 1.4,
                        yy - 3.2,
                        width + 2.8,
                        7.1,
                        fill=1,
                        stroke=0,
                    )
                    self.canvas.setFillColor(colors.HexColor("#111827"))
                    self.canvas.drawCentredString(note_x, yy - 2.3, text)
                    if event.score.tie_out:
                        self.canvas.setStrokeColor(colors.HexColor("#4B5563"))
                        path = self.canvas.beginPath()
                        path.moveTo(note_x + 4, yy - 4)
                        path.curveTo(
                            note_x + 9,
                            yy - 9,
                            measure_x + measure_width - 4,
                            yy - 9,
                            measure_x + measure_width - 1,
                            yy - 4,
                        )
                        self.canvas.drawPath(path, stroke=1, fill=0)

            technique_draws, condensed = _layout_technique_labels(
                technique_placements,
                base_y=tab_top + 16,
            )
            self.canvas.setFillColor(colors.HexColor("#1F4B73"))
            self.canvas.setFont("Helvetica-Oblique", 5.4)
            for draw in technique_draws:
                self.canvas.drawCentredString(draw.x, draw.y, draw.text)
            if condensed:
                warning = (
                    "Dense repeated technique labels were condensed in the PDF; "
                    "complete event-level intent remains in Guitar IR."
                )
                if warning not in self.warnings:
                    self.warnings.append(warning)

        self.canvas.setStrokeColor(colors.HexColor("#111827"))
        self.canvas.setLineWidth(0.9)
        self.canvas.line(x1, tab_top + 1, x1, tab_bottom - 1)
        return tab_bottom - (82 if has_voice_two else 48)

    def draw_tracks(self) -> None:
        for track in self.project.tracks:
            section = track.name or track.id
            harmony_labels = _harmony_label_map(track)
            self._new_page(section)
            self.canvas.setFillColor(colors.HexColor("#111827"))
            self.canvas.setFont("Helvetica-Bold", 15)
            self.canvas.drawString(self.margin_x, self.current_y, section)
            self.current_y -= 16
            self.canvas.setFont("Helvetica", 7.8)
            self.canvas.setFillColor(colors.HexColor("#4B5563"))
            source_text = track.source_stream_id or "manual track"
            self.canvas.drawString(
                self.margin_x,
                self.current_y,
                f"{source_text} | role {track.role} | {len(track.measures)} measures | {track.fret_count} frets",
            )
            self.current_y -= 22
            systems = 0
            for offset in range(0, len(track.measures), self.measures_per_system):
                chunk = track.measures[offset : offset + self.measures_per_system]
                minimum_start_y = 175 if _system_uses_voice_two(chunk) else 140
                if (
                    systems >= self.systems_per_page
                    or self.current_y < minimum_start_y
                ):
                    self._new_page(section)
                    systems = 0
                self.current_y = self._draw_system(
                    chunk,
                    self.current_y,
                    harmony_labels,
                ) - 8
                systems += 1

    def save(self) -> None:
        self._draw_footer()
        self.canvas.save()


def export_score_pdf(
    project: GuitarProjectIR,
    output: str | Path,
    *,
    measures_per_system: int = 4,
    systems_per_page: int = 5,
) -> PDFScoreExportResult:
    """Render Guitar IR into a landscape A4 PDF TAB score."""

    if not project.tracks:
        raise ValueError("The Guitar IR contains no tracks.")
    if measures_per_system < 1:
        raise ValueError("measures_per_system must be at least one.")
    if systems_per_page < 1:
        raise ValueError("systems_per_page must be at least one.")

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    renderer = _PDFScoreRenderer(
        project,
        destination,
        measures_per_system=measures_per_system,
        systems_per_page=systems_per_page,
    )
    renderer.draw_cover()
    renderer.draw_tracks()
    renderer.save()

    return PDFScoreExportResult(
        path=str(destination),
        page_count=renderer.page_count,
        track_count=len(project.tracks),
        measure_count=sum(len(track.measures) for track in project.tracks),
        note_count=sum(
            len(measure.events)
            for track in project.tracks
            for measure in track.measures
        ),
        maximum_voice_count=_maximum_voice_count(project),
        warnings=renderer.warnings,
    )
