from __future__ import annotations

from io import BytesIO
from pathlib import Path
import time

import mido
from fastapi.testclient import TestClient

from fretpilot.ai.models import AIProviderIdentity
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


def _layered_guitar_and_piano_midi() -> bytes:
    output = BytesIO()
    midi = mido.MidiFile(type=1, ticks_per_beat=480)

    guitar = mido.MidiTrack()
    guitar.append(mido.MetaMessage("track_name", name="Guitar Layers", time=0))
    guitar.append(mido.Message("program_change", program=25, channel=0, time=0))
    for pitch in [64, 66, 67, 69]:
        guitar.append(mido.Message("note_on", note=pitch, velocity=90, time=0))
        guitar.append(mido.Message("note_off", note=pitch, velocity=0, time=240))
    guitar.append(mido.Message("program_change", program=28, channel=0, time=0))
    for pitch in [69, 67, 66, 64]:
        guitar.append(mido.Message("note_on", note=pitch, velocity=90, time=0))
        guitar.append(mido.Message("note_off", note=pitch, velocity=0, time=240))
    midi.tracks.append(guitar)

    piano = mido.MidiTrack()
    piano.append(mido.MetaMessage("track_name", name="Piano", time=0))
    piano.append(mido.Message("program_change", program=0, channel=1, time=0))
    for pitch in [48, 55, 60, 64, 67, 72, 76, 79]:
        piano.append(mido.Message("note_on", note=pitch, velocity=80, time=0))
        piano.append(mido.Message("note_off", note=pitch, velocity=0, time=240))
    midi.tracks.append(piano)

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


def test_api_reports_when_ai_is_not_configured(tmp_path: Path) -> None:
    app = create_app(
        job_root=tmp_path,
        configure_ai_from_environment=False,
    )
    with TestClient(app) as client:
        response = client.get("/api/ai/status")

    assert response.status_code == 200
    assert response.json() == {
        "configured": False,
        "mode": "shadow",
        "configuration_error": None,
    }


def test_api_ai_shadow_requires_consent_and_never_applies_advice(
    tmp_path: Path,
) -> None:
    class FakeAdvisor:
        identity = AIProviderIdentity(
            "fixture-provider",
            "fixture-model",
            "https://llm.example",
        )

        def __init__(self):
            self.calls = 0

        def propose_rewrite(self, request):
            self.calls += 1
            return {"summary": "No confident change.", "decisions": []}

    advisor = FakeAdvisor()
    app = create_app(job_root=tmp_path, ai_advisor=advisor)
    with TestClient(app) as client:
        status_response = client.get("/api/ai/status")
        without_consent = client.post(
            "/api/ai/shadow",
            files={"midi_file": ("riff.mid", _guitar_midi(), "audio/midi")},
        )
        shadow_response = client.post(
            "/api/ai/shadow",
            files={"midi_file": ("riff.mid", _guitar_midi(), "audio/midi")},
            data={"consent_external_ai": "true", "midi_fidelity": "0.35"},
        )

    assert status_response.status_code == 200
    assert status_response.json()["provider"] == {
        "provider_id": "fixture-provider",
        "model": "fixture-model",
        "endpoint_origin": "https://llm.example",
    }
    assert without_consent.status_code == 422
    assert shadow_response.status_code == 200
    payload = shadow_response.json()
    assert payload["mode"] == "shadow"
    assert payload["applied"] is False
    assert payload["source_label"] == "riff.mid"
    assert advisor.calls == 1
    assert list((tmp_path / "ai-shadow").glob("*/source.mid")) == []


def test_api_lists_virtual_instrument_knowledge_profiles(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get("/api/virtual-instruments")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot_version"] == "2026.08.0"
    assert payload["profiles"] == [
        {
            "profile_id": "ample-metal-eclipse-v4.1",
            "vendor": "Ample Sound",
            "product": "Ample Metal Eclipse",
            "version_family": "4.1",
            "maturity": "official_documented",
            "verification_status": "plugin_unverified",
            "playable_range": {"minimum": 36, "maximum": 84},
            "articulation_intents": [
                "sustain",
                "pop",
                "natural_harmonic",
                "palm_mute",
                "slide_in",
                "slide_out",
                "legato_slide",
                "hammer_on",
                "pull_off",
                "tap",
                "pinch_harmonic",
            ],
        }
    ]


def test_api_exposes_full_knowledge_entries_for_human_review(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get("/api/knowledge")

    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot_version"] == "2026.08.2"
    assert payload["status"] == "approved"
    assert len(payload["entries"]) == 81
    metal = next(
        entry for entry in payload["entries"]
        if entry["knowledge_id"] == "gk.profile.metal"
    )
    assert metal["payload"]["articulation"]["palm_mute"] == 1.6
    assert metal["provenance"]["source_type"] == "hand_authored"


def test_api_exposes_full_virtual_instrument_profile_for_review(tmp_path: Path) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get(
            "/api/virtual-instruments/ample-metal-eclipse-v4.1"
        )

    assert response.status_code == 200
    profile = response.json()
    assert profile["knowledge_version"] == "2026.08.0"
    assert profile["verification_status"] == "plugin_unverified"
    assert len(profile["capabilities"]) == 11
    action = profile["capabilities"][7]["actions"][0]
    assert action["kind"] == "keyswitch"
    assert action["target"] == 29
    assert action["timing"] == "before_source_note"
    assert action["display_label"] == "F0"
    assert action["state"] == "momentary"
    assert action["release_value"] is None
    assert action["offset_ticks"] == 0
    assert profile["evidence"][0]["status"] == "official"


def test_api_returns_not_found_for_unknown_virtual_instrument_profile(
    tmp_path: Path,
) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.get("/api/virtual-instruments/not-a-profile")

    assert response.status_code == 404


def test_detection_preflight_groups_guitar_program_fragments_and_filters_piano(
    tmp_path: Path,
) -> None:
    with TestClient(create_app(job_root=tmp_path)) as client:
        response = client.post(
            "/api/detect",
            files={
                "midi_file": (
                    "layers.mid",
                    _layered_guitar_and_piano_midi(),
                    "audio/midi",
                )
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_filename"] == "layers.mid"
    assert payload["total_stream_count"] == 3
    assert payload["guitar_part_count"] == 1
    assert payload["selected_stream_count"] == 2
    assert payload["filtered_count"] == 1
    assert payload["possible_count"] + payload["unlikely_count"] == 1
    assert len(payload["candidates"]) == 1
    candidate = payload["candidates"][0]
    assert candidate["source_track_name"] == "Guitar Layers"
    assert candidate["fragment_count"] == 2
    assert candidate["guitar_probability"] >= 0.75
    assert candidate["confidence"] >= 0.5
    assert "按一个吉他声部展示" in candidate["reasons"][-1]
    assert list((tmp_path / "detections").glob("*/source.mid")) == []


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
        assert job["knowledge_snapshot_version"] == "2026.08.2"
        assert len(job["streams"]) == 1
        assert job["detection"]["guitar_part_count"] == 1
        assert job["detection"]["filtered_count"] == 0
        assert job["streams"][0]["source_track_name"] == "Electric Guitar"
        assert job["streams"][0]["guitar_probability"] >= 0.75
        assert job["streams"][0]["confidence"] >= 0.5
        assert job["streams"][0]["recommendation"] == "optional"

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
