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

from fretpilot.midi import load_midi
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
    status: str = "queued"
    progress: int = 0
    error: str | None = None
    created_at: str = field(default_factory=_now)
    completed_at: str | None = None
    streams: list[StreamRecord] = field(default_factory=list)


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
            manifest = generate_prototype_package(
                timeline,
                record.output_directory,
                all_likely_guitars=True,
                midi_fidelity=record.midi_fidelity,
                include_pdf=record.requested_outputs.pdf,
                include_gp5=record.requested_outputs.gp5,
                include_ample_sc_midi=record.requested_outputs.ample_sc_midi,
            )
            streams = [self._collect_stream(job_id, item) for item in manifest.stream_results]
            with self._lock:
                record.streams = streams
                record.status = "completed"
                record.progress = 100
                record.completed_at = _now()
        except Exception as exc:  # API jobs must surface engine failures as state.
            with self._lock:
                record.status = "failed"
                record.progress = 100
                record.error = str(exc) or type(exc).__name__
                record.completed_at = _now()

    def _collect_stream(self, job_id: str, result: Any) -> StreamRecord:
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
        if result.report.path:
            report_path = Path(result.report.path)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            review_required = bool(report.get("review_required"))
        return StreamRecord(
            stream_id=result.stream_id,
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
                "error": record.error,
                "created_at": record.created_at,
                "completed_at": record.completed_at,
                "streams": [
                    {
                        "stream_id": stream.stream_id,
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
