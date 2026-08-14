"""Density-aware public PDF exporter built on the stable core renderer.

This compatibility layer deliberately reuses the existing drawing implementation
for harmony, rests, stems, beams, dots, tuplets, techniques, and ties. It changes
only how many measures share a system. Dense passages get wider equal-width
measures by using fewer measures per line, while beat positions inside each
measure remain strictly time-proportional in the core renderer.
"""

from __future__ import annotations

from pathlib import Path

from fretpilot.exporters.pdf_score.layout import (
    DEFAULT_MIN_ONSET_GAP,
    chunk_measures_for_equal_width_systems,
    measure_required_width,
)
from fretpilot.exporters.pdf_score.renderer import (
    PDFScoreExportResult,
    _PDFScoreRenderer,
    _harmony_label_map,
)
from fretpilot.ir.models import GuitarProjectIR, GuitarTrackIR


def _system_available_width(renderer: _PDFScoreRenderer) -> float:
    x0 = renderer.margin_x + 38.0
    x1 = renderer.width - renderer.margin_x
    return x1 - x0


def _track_system_chunks(
    track: GuitarTrackIR,
    *,
    max_measures_per_system: int,
    available_width: float,
) -> list[list]:
    return chunk_measures_for_equal_width_systems(
        track.measures,
        max_measures_per_system=max_measures_per_system,
        available_width=available_width,
    )


def _density_warnings(
    track: GuitarTrackIR,
    *,
    available_width: float,
) -> list[str]:
    warnings: list[str] = []
    for measure in track.measures:
        required = measure_required_width(measure)
        if required <= available_width + 1e-7:
            continue
        warnings.append(
            f"Measure {measure.number} in {track.name or track.id} requires about "
            f"{required:.1f} pt to preserve the {DEFAULT_MIN_ONSET_GAP:.1f} pt "
            f"minimum onset gap, but one PDF system provides {available_width:.1f} pt. "
            "The measure remains time-proportional but will be horizontally compressed."
        )
    return warnings


class _DensityAwarePDFScoreRenderer(_PDFScoreRenderer):
    """Reuse core engraving while changing only density-sensitive line breaks."""

    def draw_tracks(self) -> None:
        max_measures = self.measures_per_system
        available_width = _system_available_width(self)

        for track in self.project.tracks:
            for warning in _density_warnings(track, available_width=available_width):
                if warning not in self.warnings:
                    self.warnings.append(warning)

            section = track.name or track.id
            harmony_labels = _harmony_label_map(track)
            self._new_page(section)
            self.canvas.setFillColorRGB(17 / 255, 24 / 255, 39 / 255)
            self.canvas.setFont("Helvetica-Bold", 15)
            self.canvas.drawString(self.margin_x, self.current_y, section)
            self.current_y -= 16
            self.canvas.setFont("Helvetica", 7.8)
            self.canvas.setFillColorRGB(75 / 255, 85 / 255, 99 / 255)
            source_text = track.source_stream_id or "manual track"
            self.canvas.drawString(
                self.margin_x,
                self.current_y,
                f"{source_text} | role {track.role} | {len(track.measures)} measures | {track.fret_count} frets",
            )
            self.current_y -= 22

            systems = 0
            chunks = _track_system_chunks(
                track,
                max_measures_per_system=max_measures,
                available_width=available_width,
            )
            for chunk in chunks:
                if systems >= self.systems_per_page or self.current_y < 140:
                    self._new_page(section)
                    systems = 0

                self.measures_per_system = len(chunk)
                try:
                    self.current_y = self._draw_system(
                        chunk,
                        self.current_y,
                        harmony_labels,
                    ) - 8
                finally:
                    self.measures_per_system = max_measures
                systems += 1


def export_score_pdf(
    project: GuitarProjectIR,
    output: str | Path,
    *,
    measures_per_system: int = 4,
    systems_per_page: int = 5,
) -> PDFScoreExportResult:
    """Render Guitar IR with density-aware system breaking."""

    if not project.tracks:
        raise ValueError("The Guitar IR contains no tracks.")
    if measures_per_system < 1:
        raise ValueError("measures_per_system must be at least one.")
    if systems_per_page < 1:
        raise ValueError("systems_per_page must be at least one.")

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    renderer = _DensityAwarePDFScoreRenderer(
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
