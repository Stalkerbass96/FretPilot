from __future__ import annotations

from io import BytesIO
from pathlib import Path
import time

import mido
from fastapi.testclient import TestClient

from fretpilot.api import create_app


def _guitar_midi() -> bytes:
    output = BytesIO()
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    midi.tracks.append(track)
    track.append(mido.MetaMessage("track_name", name="Electric Guitar", time=0))
    track.append(mido.Message("program_change", program=27, channel=0, time=0))
    pitches = [64, 66, 67, 69, 67, 66, 64, 64]
    for pitch in pitches:
        track.append(mido.Message("note_on", note=pitch, velocity=90, time=0))
        track.append(mido.Message("note_off", note=pitch, velocity=0, time=240))
    midi.save(file=output)
    return output.getvalue()


def _wait_for_job(client: TestClient, job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.02)
    raise AssertionError("API job did not finish")


def test_health_reports_ready_engine(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "engine": "fretpilot"}


def test_job_runs_real_engine_and_exposes_selected_downloads(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.post(
            "/api/jobs",
            files={"midi_file": ("riff.mid", _guitar_midi(), "audio/midi")},
            data={
                "midi_fidelity": "0.35",
                "include_pdf": "false",
                "include_gp5": "true",
                "include_ample_sc_midi": "true",
            },
        )
        assert response.status_code == 202

        job = _wait_for_job(client, response.json()["id"])
        assert job["status"] == "completed", job.get("error")
        assert job["source_filename"] == "riff.mid"
        assert job["midi_fidelity"] == 0.35
        assert len(job["streams"]) == 1

        artifacts = job["streams"][0]["artifacts"]
        assert {artifact["kind"] for artifact in artifacts} == {"gp5", "ample_sc_midi"}
        for artifact in artifacts:
            download = client.get(artifact["download_url"])
            assert download.status_code == 200
            assert download.content


def test_job_rejects_invalid_upload_and_empty_output_selection(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path, max_upload_bytes=16)) as client:
        wrong_extension = client.post(
            "/api/jobs",
            files={"midi_file": ("notes.txt", b"not midi", "text/plain")},
        )
        no_outputs = client.post(
            "/api/jobs",
            files={"midi_file": ("riff.mid", _guitar_midi(), "audio/midi")},
            data={
                "include_pdf": "false",
                "include_gp5": "false",
                "include_ample_sc_midi": "false",
            },
        )
        too_large = client.post(
            "/api/jobs",
            files={"midi_file": ("large.mid", b"x" * 17, "audio/midi")},
        )

    assert wrong_extension.status_code == 415
    assert no_outputs.status_code == 422
    assert too_large.status_code == 413


def test_artifact_ids_cannot_read_arbitrary_files(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("private", encoding="utf-8")
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get("/api/jobs/missing/artifacts/../../secret.txt")

    assert response.status_code == 404
