"""Render canonical Guitar IR as a review-friendly PDF TAB score.

The PDF output is intentionally independent of Guitar Pro. V0.1 renders six-line
TAB, measure positions, duration labels, ties, and generic guitar techniques.
It is designed for review and prototype validation rather than final publishing.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from fretpilot.ir.models import GuitarMeasure, GuitarNoteEvent, GuitarProjectIR


@dataclass(slots=True)
class PDFScoreExportResult:
    path: str
    page_count: int
    track_count: int
    measure_count: int
    note_count: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "page_count": self.page_count,
            "track_count": self.track_count,
            "measure_count": self.measure_count,
            "note_count": self.note_count,
            "warnings": self.warnings,
        }


def _duration_label(beats: float) -> str:
    candidates = [
        (4.0, "1"),
        (3.0, "1/2."),
        (2.0, "1/2"),
        (1.5, "1/4."),
        (1.0, "1/4"),
        (0.75, "1/8."),
        (2 / 3, "4T"),
        (0.5, "1/8"),
        (1 / 3, "8T"),
        (0.25, "1/16"),
        (1 / 6, "16T"),
        (0.125, "1/32"),
    ]
    return min(candidates, key=lambda item: abs(item[0] - beats))[1]


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
    }
    labels: list[str] = []
    for articulation in event.articulations:
        label = mapping.get(articulation.type, articulation.type.replace("_", " "))
        if label not in labels:
            labels.append(label)
    return labels


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
            "Duration labels: 1/4 quarter, 1/8 eighth, 1/16 sixteenth, 8T eighth-note triplet.",
            "Technique labels: H hammer-on, P pull-off, S slide, LS legato slide, vib., let ring, P.M.",
            "Fret numbers are positioned on standard six-line TAB. Ties are drawn at measure boundaries.",
            "This V0.1 PDF is a review format; standard notation and advanced engraving remain future work.",
        ]
        for line in legend:
            self.canvas.drawString(self.margin_x, y, line)
            y -= 16

    def _draw_system(
        self,
        measures: list[GuitarMeasure],
        y: float,
    ) -> float:
        x0 = self.margin_x + 38
        x1 = self.width - self.margin_x
        measure_width = (x1 - x0) / self.measures_per_system
        line_gap = 8.2
        tab_top = y - 27
        tab_bottom = tab_top - 5 * line_gap
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

            grouped: dict[float, list[GuitarNoteEvent]] = defaultdict(list)
            for event in measure.events:
                grouped[round(event.score.start_beat, 7)].append(event)

            for absolute_start, events in sorted(grouped.items()):
                beat_in_measure = absolute_start - measure.start_beat
                ratio = max(0.0, min(1.0, beat_in_measure / measure.duration_beats))
                note_x = measure_x + 7 + (measure_width - 14) * ratio
                duration = min(event.score.duration_beats for event in events)
                self.canvas.setFillColor(colors.HexColor("#374151"))
                self.canvas.setFont("Helvetica", 5.8)
                self.canvas.drawCentredString(
                    note_x,
                    tab_top + 2.5,
                    _duration_label(duration),
                )

                labels: list[str] = []
                for event in events:
                    for label in _technique_label(event):
                        if label not in labels:
                            labels.append(label)
                if labels:
                    self.canvas.setFillColor(colors.HexColor("#1F4B73"))
                    self.canvas.setFont("Helvetica-Oblique", 5.4)
                    self.canvas.drawCentredString(
                        note_x,
                        tab_top + 17,
                        ", ".join(labels[:3]),
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

        self.canvas.setStrokeColor(colors.HexColor("#111827"))
        self.canvas.setLineWidth(0.9)
        self.canvas.line(x1, tab_top + 1, x1, tab_bottom - 1)
        return tab_bottom - 21

    def draw_tracks(self) -> None:
        for track in self.project.tracks:
            section = track.name or track.id
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
                if systems >= self.systems_per_page or self.current_y < 115:
                    self._new_page(section)
                    systems = 0
                chunk = track.measures[offset : offset + self.measures_per_system]
                self.current_y = self._draw_system(chunk, self.current_y) - 8
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
        warnings=renderer.warnings,
    )
