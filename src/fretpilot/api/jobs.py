"""In-process conversion jobs for the local FretPilot API."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from fretpilot.detection import classify_timeline
from fretpilot.detection.review import build_guitar_review_summary
from fretpilot.midi import load_midi
from fretpilot.knowledge import BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
from fretpilot.prototype import PrototypeOutputStatus, generate_prototype_package


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class OutputRequest:
    pdf: bool
    gp5: bool
    ample_sc_midi: bool

    def to_dict(self) -> dict[str, bool]:
        return {
            "pdf": self.pdf,
            "gp5": self.gp5,
            "ample_sc_midi": self.ample_sc_midi,
        }


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    id: str
    kind: str
    name: str
    path: Path
    size_bytes: int

    def to_public_dict(self, job_id: str) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "size_bytes": self.size_bytes,
            "download_url": f"/api/jobs/{job_id}/artifacts/{self.id}",
        }


@dataclass(slots=True)
class StreamRecord:
    stream_id: str
    group_id: str = ""
    source_track_name: str = ""
    display_channel: int = 0
    program_name: str | None = None
    note_count: int = 0
    guitar_probability: float = 0.0
    confidence: float = 0.0
    recommendation: str = "review"
    recommendation_text: str = ""
    reasons: list[str] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    review_required: bool = False


@dataclass(slots=True)
class JobRecord:
    id: str
    source_filename: str
    midi_fidelity: float
    requested_outputs: OutputRequest
    source_path: Path
    output_directory: Path
    knowledge_snapshot_version: str = BUILTIN_KNOWLEDGE_SNAPSHOT_VERSION
    status: str = "queued"
    progress: int = 0
    error: str | None = None
    created_at: str = field(default_factory=_now)
    completed_at: str | None = None
    streams: list[StreamRecord] = field(default_factory=list)
    detection_summary: dict[str, Any] | None = None


class JobManager:
    """Own a bounded worker pool and an in-memory index of local jobs."""

    def __init__(self, job_root: Path, *, max_workers: int = 2) -> None:
        self.job_root = job_root.resolve()
        self.job_root.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="fretpilot-job",
        )

    def submit(
        self,
        *,
        job_id: str,
        source_filename: str,
        source_path: Path,
        output_directory: Path,
        midi_fidelity: float,
        requested_outputs: OutputRequest,
    ) -> dict[str, Any]:
        record = JobRecord(
            id=job_id,
            source_filename=source_filename,
            midi_fidelity=midi_fidelity,
            requested_outputs=requested_outputs,
            source_path=source_path,
            output_directory=output_directory,
        )
        with self._lock:
            self._jobs[job_id] = record
        self._executor.submit(self._run, job_id)
        return self.snapshot(job_id)

    def _run(self, job_id: str) -> None:
        with self._lock:
            record = self._jobs[job_id]
            record.status = "processing"
            record.progress = 10

        try:
            timeline = load_midi(record.source_path)
            detection_summary = build_guitar_review_summary(
                classify_timeline(timeline)
            )
            metadata_by_stream = {
                stream_id: candidate
                for candidate in detection_summary["candidates"]
                for stream_id in candidate["stream_ids"]
            }
            manifest = generate_prototype_package(
                timeline,
                record.output_directory,
                all_likely_guitars=True,
                midi_fidelity=record.midi_fidelity,
                include_pdf=record.requested_outputs.pdf,
                include_gp5=record.requested_outputs.gp5,
                include_ample_sc_midi=record.requested_outputs.ample_sc_midi,
            )
            streams = [
                self._collect_stream(
                    job_id,
                    item,
                    metadata_by_stream.get(item.stream_id, {}),
                )
                for item in manifest.stream_results
            ]
            with self._lock:
                record.knowledge_snapshot_version = manifest.knowledge_snapshot_version
                record.streams = streams
                record.detection_summary = detection_summary
                record.status = "completed"
                record.progress = 100
                record.completed_at = _now()
        except Exception as exc:  # API jobs must surface engine failures as state.
            with self._lock:
                record.status = "failed"
                record.progress = 100
                record.error = str(exc) or type(exc).__name__
                record.completed_at = _now()

    def _collect_stream(
        self,
        job_id: str,
        result: Any,
        candidate_summary: dict[str, Any],
    ) -> StreamRecord:
        artifacts: list[ArtifactRecord] = []
        outputs: list[dict[str, Any]] = []
        requested = (
            ("pdf", result.pdf),
            ("gp5", result.gp5),
            ("ample_sc_midi", result.ample_sc_midi),
        )
        for kind, status in requested:
            artifact = self._artifact_for(job_id, kind, status)
            if artifact is not None:
                artifacts.append(artifact)
            outputs.append(
                {
                    "kind": kind,
                    "status": status.status,
                    "warnings": status.warnings,
                    "error": status.error,
                    "artifact_id": artifact.id if artifact else None,
                }
            )

        review_required = False
        stream_summary: dict[str, Any] = {}
        if result.report.path:
            report_path = Path(result.report.path)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            review_required = bool(report.get("review_required"))
            stream_summary = dict(report.get("stream", {}))
        return StreamRecord(
            stream_id=result.stream_id,
            group_id=str(candidate_summary.get("group_id", result.stream_id)),
            source_track_name=str(
                stream_summary.get("source_track_name", result.stream_id)
            ),
            display_channel=int(stream_summary.get("display_channel", 0)),
            program_name=stream_summary.get("program_name"),
            note_count=int(stream_summary.get("note_count", 0)),
            guitar_probability=float(
                candidate_summary.get("guitar_probability", 0.0)
            ),
            confidence=float(candidate_summary.get("confidence", 0.0)),
            recommendation=str(candidate_summary.get("recommendation", "review")),
            recommendation_text=str(
                candidate_summary.get("recommendation_text", "")
            ),
            reasons=list(candidate_summary.get("reasons", [])),
            outputs=outputs,
            artifacts=artifacts,
            review_required=review_required,
        )

    def _artifact_for(
        self,
        job_id: str,
        kind: str,
        status: PrototypeOutputStatus,
    ) -> ArtifactRecord | None:
        if status.status != "success" or status.path is None:
            return None
        path = Path(status.path).resolve()
        job_directory = (self.job_root / job_id).resolve()
        if not path.is_relative_to(job_directory) or not path.is_file():
            raise ValueError("Generated artifact escaped its job directory.")
        return ArtifactRecord(
            id=uuid4().hex,
            kind=kind,
            name=path.name,
            path=path,
            size_bytes=path.stat().st_size,
        )

    def snapshot(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            return {
                "id": record.id,
                "status": record.status,
                "progress": record.progress,
                "source_filename": record.source_filename,
                "midi_fidelity": record.midi_fidelity,
                "requested_outputs": record.requested_outputs.to_dict(),
                "knowledge_snapshot_version": record.knowledge_snapshot_version,
                "error": record.error,
                "created_at": record.created_at,
                "completed_at": record.completed_at,
                "detection": (
                    dict(record.detection_summary)
                    if record.detection_summary is not None
                    else None
                ),
                "streams": [
                    {
                        "stream_id": stream.stream_id,
                        "group_id": stream.group_id,
                        "source_track_name": stream.source_track_name,
                        "display_channel": stream.display_channel,
                        "program_name": stream.program_name,
                        "note_count": stream.note_count,
                        "guitar_probability": stream.guitar_probability,
                        "confidence": stream.confidence,
                        "recommendation": stream.recommendation,
                        "recommendation_text": stream.recommendation_text,
                        "reasons": list(stream.reasons),
                        "review_required": stream.review_required,
                        "outputs": [dict(output) for output in stream.outputs],
                        "artifacts": [
                            artifact.to_public_dict(job_id)
                            for artifact in stream.artifacts
                        ],
                    }
                    for stream in record.streams
                ],
            }

    def artifact(self, job_id: str, artifact_id: str) -> ArtifactRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            for stream in record.streams:
                for artifact in stream.artifacts:
                    if artifact.id == artifact_id:
                        return artifact
        raise KeyError(artifact_id)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=False)
