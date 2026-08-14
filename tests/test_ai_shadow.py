from __future__ import annotations

import json
from pathlib import Path

import httpx
import mido

from fretpilot.ai.context import build_shadow_policy, build_shadow_rewrite_request
from fretpilot.ai.models import AIProviderIdentity
from fretpilot.ai.providers.openai_compatible import (
    OpenAICompatibleRewriteAdvisor,
)
from fretpilot.ai.shadow import generate_shadow_rewrite_report
from fretpilot.cli import main
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.models import (
    NormalizedNote,
    NormalizedTimeline,
    TempoEvent,
    TimeSignatureEvent,
)
from fretpilot.rewrite import rewrite_instrument_stream


def _fixture() -> tuple[NormalizedTimeline, InstrumentStream]:
    notes = [
        NormalizedNote(
            track_index=0,
            track_name="Guitar",
            channel=0,
            pitch=40 + index,
            velocity=90,
            start_tick=index * 120,
            duration_ticks=96,
            start_beat=index * 0.25,
            duration_beats=0.2,
            program=29,
        )
        for index in range(8)
    ]
    stream = InstrumentStream(
        stream_id="t0:ch0:p29",
        source_track_index=0,
        source_track_name="Guitar",
        channel=0,
        program=29,
        program_name="Overdriven Guitar",
        program_family="guitar",
        instrument_name="Guitar",
        notes=notes,
    )
    timeline = NormalizedTimeline(
        source="/private/music/example.mid",
        midi_type=1,
        ticks_per_beat=480,
        tempo_events=[TempoEvent(0, 0.0, 120.0)],
        time_signature_events=[TimeSignatureEvent(0, 0.0, 4, 4)],
        tracks=[],
    )
    return timeline, stream


class _FakeAdvisor:
    identity = AIProviderIdentity("test", "fixture-model", "https://llm.test")

    def propose_rewrite(self, request):
        return {
            "summary": "One deletion and one octave move may simplify the phrase.",
            "decisions": [
                {
                    "source_note_index": 0,
                    "operation": "delete",
                    "confidence": 0.82,
                    "reason": "The first note is treated as a weak pickup.",
                },
                {
                    "source_note_index": 1,
                    "operation": "transpose",
                    "target_pitch": 53,
                    "confidence": 0.88,
                    "reason": "An octave move keeps the phrase in one position.",
                },
                {
                    "source_note_index": 2,
                    "operation": "transpose",
                    "target_pitch": 100,
                    "confidence": 0.75,
                    "reason": "This intentionally violates the policy.",
                },
            ],
        }


def test_fidelity_policy_removes_all_ai_edit_authority_at_one():
    policy = build_shadow_policy(
        1.0,
        context_note_count=100,
        max_context_notes=256,
    )
    assert policy.allowed_operations == ()
    assert policy.max_delete_count == 0
    assert policy.max_transpose_count == 0
    assert policy.max_pitch_shift == 0


def test_shadow_report_validates_proposals_and_never_applies_them():
    timeline, stream = _fixture()
    original_pitches = [note.pitch for note in stream.notes]

    report = generate_shadow_rewrite_report(
        timeline,
        stream,
        _FakeAdvisor(),
        midi_fidelity=0.35,
    )

    assert report.applied is False
    assert [item.operation for item in report.accepted_decisions] == [
        "delete",
        "transpose",
    ]
    assert len(report.rejected_decisions) == 1
    assert "target_pitch exceeds" in " ".join(report.rejected_decisions[0].errors)
    assert [note.pitch for note in stream.notes] == original_pitches
    payload = report.to_dict()
    assert payload["mode"] == "shadow"
    assert payload["source_label"] == "example.mid"
    assert "/private/music" not in json.dumps(payload)


def test_context_is_bounded_and_records_truncation():
    timeline, stream = _fixture()
    baseline = rewrite_instrument_stream(
        stream,
        midi_fidelity=0.35,
        ticks_per_beat=timeline.ticks_per_beat,
    )
    request = build_shadow_rewrite_request(
        timeline,
        stream,
        baseline,
        max_context_notes=4,
    )

    assert len(request.notes) == 4
    assert request.context_truncated is True
    assert request.source_label == "example.mid"


def test_openai_compatible_provider_uses_structured_chat_completion():
    timeline, stream = _fixture()
    baseline = rewrite_instrument_stream(
        stream,
        midi_fidelity=0.35,
        ticks_per_beat=timeline.ticks_per_beat,
    )
    request = build_shadow_rewrite_request(timeline, stream, baseline)
    observed: dict[str, object] = {}

    def handler(http_request: httpx.Request) -> httpx.Response:
        observed["url"] = str(http_request.url)
        observed["authorization"] = http_request.headers["Authorization"]
        observed["body"] = json.loads(http_request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"summary\":\"No change\",\"decisions\":[]}\n```"
                        }
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleRewriteAdvisor(
            base_url="https://llm.example/v1",
            api_key="secret-test-key",
            model="example-model",
            client=client,
        )
        result = provider.propose_rewrite(request)

    assert result == {"summary": "No change", "decisions": []}
    assert observed["url"] == "https://llm.example/v1/chat/completions"
    assert observed["authorization"] == "Bearer secret-test-key"
    assert observed["body"]["response_format"] == {"type": "json_object"}
    assert provider.identity.endpoint_origin == "https://llm.example"


def test_ai_shadow_cli_reads_secret_from_environment_and_writes_report(
    tmp_path: Path,
    monkeypatch,
):
    midi_path = tmp_path / "riff.mid"
    midi = mido.MidiFile(type=0, ticks_per_beat=480)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name="Guitar", time=0))
    track.append(mido.Message("program_change", channel=0, program=29, time=0))
    for index in range(16):
        track.append(
            mido.Message(
                "note_on",
                channel=0,
                note=52 + index % 4,
                velocity=90,
                time=0 if index == 0 else 24,
            )
        )
        track.append(
            mido.Message("note_off", channel=0, note=52 + index % 4, time=96)
        )
    midi.tracks.append(track)
    midi.save(midi_path)

    class FakeConfiguredAdvisor:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "environment-secret"
            self.identity = AIProviderIdentity(
                kwargs["provider_id"],
                kwargs["model"],
                "https://llm.example",
            )

        def propose_rewrite(self, request):
            return {"summary": "No confident change.", "decisions": []}

    monkeypatch.setattr(
        "fretpilot.cli.OpenAICompatibleRewriteAdvisor",
        FakeConfiguredAdvisor,
    )
    monkeypatch.setenv("TEST_FRETPILOT_LLM_KEY", "environment-secret")
    output = tmp_path / "shadow.json"

    assert main(
        [
            "ai-shadow",
            str(midi_path),
            "--base-url",
            "https://llm.example/v1",
            "--model",
            "fixture-model",
            "--provider-id",
            "fixture-provider",
            "--api-key-env",
            "TEST_FRETPILOT_LLM_KEY",
            "-o",
            str(output),
        ]
    ) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["applied"] is False
    assert payload["provider"]["provider_id"] == "fixture-provider"
    assert "environment-secret" not in output.read_text(encoding="utf-8")
