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
from starlette.concurrency import run_in_threadpool

from fretpilot.ai import generate_shadow_rewrite_report
from fretpilot.ai.config import advisor_from_environment
from fretpilot.ai.providers import AIProviderError, RewriteAdvisor
from fretpilot.api.jobs import JobManager, OutputRequest
from fretpilot.detection import classify_timeline
from fretpilot.detection.review import build_guitar_review_summary
from fretpilot.knowledge import get_builtin_knowledge_registry
from fretpilot.midi import load_midi
from fretpilot.rewrite import DEFAULT_MIDI_FIDELITY
from fretpilot.virtual_instruments import get_builtin_virtual_instrument_registry

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
    ai_advisor: RewriteAdvisor | None = None,
    configure_ai_from_environment: bool = True,
) -> FastAPI:
    root = Path(job_root) if job_root is not None else _default_job_root()
    manager = JobManager(root)
    ai_configuration_error: str | None = None
    if ai_advisor is None and configure_ai_from_environment:
        ai_advisor, ai_configuration_error = advisor_from_environment()

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

    async def save_midi_upload(
        midi_file: UploadFile,
        directory: Path,
    ) -> tuple[str, Path]:
        filename = Path(midi_file.filename or "").name
        suffix = Path(filename).suffix.lower()
        if suffix not in {".mid", ".midi"}:
            await midi_file.close()
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Please upload a .mid or .midi file.",
            )
        directory.mkdir(parents=True)
        source_path = directory / f"source{suffix}"
        total = 0
        try:
            with source_path.open("wb") as destination:
                while chunk := await midi_file.read(UPLOAD_CHUNK_BYTES):
                    total += len(chunk)
                    if total > max_upload_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=(
                                f"MIDI file exceeds the {max_upload_bytes}-byte limit."
                            ),
                        )
                    destination.write(chunk)
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise
        finally:
            await midi_file.close()
        return filename, source_path

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ready", "engine": "fretpilot"}

    @app.get("/api/knowledge")
    def get_knowledge() -> dict[str, object]:
        registry = get_builtin_knowledge_registry()
        return registry.snapshot.to_dict()

    @app.get("/api/ai/status")
    def get_ai_status() -> dict[str, object]:
        if ai_advisor is None:
            return {
                "configured": False,
                "mode": "shadow",
                "configuration_error": ai_configuration_error,
            }
        return {
            "configured": True,
            "mode": "shadow",
            "provider": {
                "provider_id": ai_advisor.identity.provider_id,
                "model": ai_advisor.identity.model,
                "endpoint_origin": ai_advisor.identity.endpoint_origin,
            },
            "transmitted_data": "bounded_structured_note_context",
            "binary_midi_transmitted": False,
        }

    @app.get("/api/virtual-instruments")
    def list_virtual_instruments() -> dict[str, object]:
        registry = get_builtin_virtual_instrument_registry()
        return {
            "snapshot_version": registry.snapshot.snapshot_version,
            "profiles": [
                {
                    "profile_id": profile.profile_id,
                    "vendor": profile.vendor,
                    "product": profile.product,
                    "version_family": profile.version_family,
                    "maturity": profile.maturity,
                    "verification_status": profile.verification_status,
                    "playable_range": {
                        "minimum": profile.playable_min,
                        "maximum": profile.playable_max,
                    },
                    "articulation_intents": [
                        capability.intent for capability in profile.capabilities
                    ],
                }
                for profile in registry.list()
            ],
        }

    @app.get("/api/virtual-instruments/{profile_id}")
    def get_virtual_instrument(profile_id: str) -> dict[str, object]:
        registry = get_builtin_virtual_instrument_registry()
        profile = registry.get(profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Virtual-instrument profile not found.",
            )
        return profile.to_dict()

    @app.post("/api/detect")
    async def detect_guitar_streams(
        midi_file: Annotated[UploadFile, File()],
    ) -> dict[str, object]:
        detection_directory = root / "detections" / uuid4().hex
        try:
            filename, source_path = await save_midi_upload(
                midi_file,
                detection_directory,
            )
            timeline = load_midi(source_path)
            summary = build_guitar_review_summary(classify_timeline(timeline))
            return {"source_filename": filename, **summary}
        finally:
            shutil.rmtree(detection_directory, ignore_errors=True)

    @app.post("/api/ai/shadow")
    async def create_ai_shadow_report(
        midi_file: Annotated[UploadFile, File()],
        consent_external_ai: Annotated[bool, Form()] = False,
        stream_id: Annotated[str | None, Form()] = None,
        midi_fidelity: Annotated[float, Form(ge=0.0, le=1.0)] = (
            DEFAULT_MIDI_FIDELITY
        ),
        max_context_notes: Annotated[int, Form(ge=1, le=512)] = 256,
    ) -> dict[str, object]:
        if not consent_external_ai:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Explicit consent is required before structured MIDI note "
                    "context is sent to an external AI provider."
                ),
            )
        if ai_advisor is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ai_configuration_error or "AI provider is not configured.",
            )

        request_directory = root / "ai-shadow" / uuid4().hex
        try:
            filename, source_path = await save_midi_upload(
                midi_file,
                request_directory,
            )
            timeline = load_midi(source_path)
            timeline.source = filename
            detection = classify_timeline(timeline)
            if stream_id is not None:
                candidate = next(
                    (
                        item
                        for item in detection.candidates
                        if item.stream.stream_id == stream_id
                    ),
                    None,
                )
                if candidate is None:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail="Requested stream_id was not found in the MIDI file.",
                    )
            else:
                likely = [
                    item
                    for item in detection.candidates
                    if item.decision == "likely_guitar"
                ]
                if len(likely) != 1:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                        detail=(
                            "AI shadow analysis requires one explicit stream_id "
                            "when guitar selection is ambiguous."
                        ),
                    )
                candidate = likely[0]
            try:
                report = await run_in_threadpool(
                    generate_shadow_rewrite_report,
                    timeline,
                    candidate.stream,
                    ai_advisor,
                    midi_fidelity=midi_fidelity,
                    max_context_notes=max_context_notes,
                )
            except (AIProviderError, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"AI shadow analysis failed: {exc}",
                ) from exc
            return report.to_dict()
        finally:
            shutil.rmtree(request_directory, ignore_errors=True)

    @app.post("/api/jobs", status_code=status.HTTP_202_ACCEPTED)
    async def create_job(
        midi_file: Annotated[UploadFile, File()],
        midi_fidelity: Annotated[float, Form(ge=0.0, le=1.0)] = DEFAULT_MIDI_FIDELITY,
        include_pdf: Annotated[bool, Form()] = True,
        include_gp5: Annotated[bool, Form()] = True,
        include_ample_sc_midi: Annotated[bool, Form()] = True,
    ) -> dict[str, object]:
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
        try:
            filename, source_path = await save_midi_upload(
                midi_file,
                source_directory,
            )
        except Exception:
            shutil.rmtree(job_directory, ignore_errors=True)
            raise

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
