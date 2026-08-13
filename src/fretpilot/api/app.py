"""FastAPI application for FretPilot's local product shell."""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
import shutil
import tempfile
from typing import Annotated, AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from fretpilot.api.jobs import JobManager, OutputRequest
from fretpilot.rewrite import DEFAULT_MIDI_FIDELITY

DEFAULT_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024


def _default_job_root() -> Path:
    configured = os.environ.get("FRETPILOT_JOB_ROOT")
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / "fretpilot-jobs"


def create_app(
    *,
    job_root: str | Path | None = None,
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
) -> FastAPI:
    root = Path(job_root) if job_root is not None else _default_job_root()
    manager = JobManager(root)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        manager.shutdown()

    app = FastAPI(
        title="FretPilot Local API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.job_manager = manager
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ready", "engine": "fretpilot"}

    @app.post("/api/jobs", status_code=status.HTTP_202_ACCEPTED)
    async def create_job(
        midi_file: Annotated[UploadFile, File()],
        midi_fidelity: Annotated[float, Form(ge=0.0, le=1.0)] = DEFAULT_MIDI_FIDELITY,
        include_pdf: Annotated[bool, Form()] = True,
        include_gp5: Annotated[bool, Form()] = True,
        include_ample_sc_midi: Annotated[bool, Form()] = True,
    ) -> dict[str, object]:
        filename = Path(midi_file.filename or "").name
        if Path(filename).suffix.lower() not in {".mid", ".midi"}:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Please upload a .mid or .midi file.",
            )
        requested = OutputRequest(
            pdf=include_pdf,
            gp5=include_gp5,
            ample_sc_midi=include_ample_sc_midi,
        )
        if not any(requested.to_dict().values()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Select at least one output format.",
            )

        job_id = uuid4().hex
        job_directory = root / job_id
        source_directory = job_directory / "input"
        output_directory = job_directory / "output"
        source_directory.mkdir(parents=True)
        source_path = source_directory / f"source{Path(filename).suffix.lower()}"
        total = 0
        try:
            with source_path.open("wb") as destination:
                while chunk := await midi_file.read(UPLOAD_CHUNK_BYTES):
                    total += len(chunk)
                    if total > max_upload_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=f"MIDI file exceeds the {max_upload_bytes}-byte limit.",
                        )
                    destination.write(chunk)
        except Exception:
            shutil.rmtree(job_directory, ignore_errors=True)
            raise
        finally:
            await midi_file.close()

        return manager.submit(
            job_id=job_id,
            source_filename=filename,
            source_path=source_path,
            output_directory=output_directory,
            midi_fidelity=midi_fidelity,
            requested_outputs=requested,
        )

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, object]:
        try:
            return manager.snapshot(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found.") from exc

    @app.get("/api/jobs/{job_id}/artifacts/{artifact_id}")
    def download_artifact(job_id: str, artifact_id: str) -> FileResponse:
        try:
            artifact = manager.artifact(job_id, artifact_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Artifact not found.") from exc
        return FileResponse(
            artifact.path,
            filename=artifact.name,
            media_type="application/octet-stream",
        )

    return app


app = create_app()
