"""Compact product-facing summaries for guitar identity review."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fretpilot.detection.models import GuitarDetectionReport, GuitarStreamCandidate


SELECTION_POLICY_VERSION = "guitar-only-v1"
SPARSE_PART_NOTE_THRESHOLD = 32


def _weighted(candidates: list[GuitarStreamCandidate], field: str) -> float:
    weights = [max(len(candidate.stream.notes), 1) for candidate in candidates]
    total = sum(weights)
    return round(
        sum(
            getattr(candidate, field) * weight
            for candidate, weight in zip(candidates, weights)
        )
        / total,
        6,
    )


def _top_reasons(candidates: list[GuitarStreamCandidate]) -> list[str]:
    reasons: list[str] = []
    if any(candidate.layers[0].status == "positive" for candidate in candidates):
        reasons.append("轨道名称明确标记为吉他。")
    guitar_programs = sorted(
        {
            candidate.stream.program_name
            for candidate in candidates
            if candidate.stream.program_family == "guitar"
            and candidate.stream.program_name
        }
    )
    if guitar_programs:
        reasons.append(f"MIDI 音色属于吉他族：{' / '.join(guitar_programs)}。")
    if len(candidates) > 1:
        reasons.append(
            f"同一轨道和通道包含 {len(candidates)} 个 Program 片段，"
            "按一个吉他声部展示。"
        )
    if all(candidate.layers[2].status == "positive" for candidate in candidates):
        reasons.append("音域、复音规模与音程运动符合六弦吉他范围。")
    return reasons[:3]


def _group_summary(candidates: list[GuitarStreamCandidate]) -> dict[str, Any]:
    candidates.sort(key=lambda item: item.stream.stream_id)
    first = candidates[0].stream
    note_count = sum(len(candidate.stream.notes) for candidate in candidates)
    recommendation = "optional" if note_count < SPARSE_PART_NOTE_THRESHOLD else "recommended"
    recommendation_text = (
        "高置信吉他，但内容很短；建议试听后决定是否保留。"
        if recommendation == "optional"
        else "高置信吉他声部，建议生成。"
    )
    programs = [
        {
            "program": candidate.stream.program,
            "program_name": candidate.stream.program_name,
        }
        for candidate in candidates
    ]
    return {
        "group_id": f"t{first.source_track_index}:ch{first.channel}",
        "source_track_index": first.source_track_index,
        "source_track_name": first.source_track_name,
        "display_channel": first.display_channel,
        "stream_ids": [candidate.stream.stream_id for candidate in candidates],
        "fragment_count": len(candidates),
        "programs": programs,
        "note_count": note_count,
        "guitar_probability": _weighted(candidates, "guitar_probability"),
        "confidence": min(candidate.confidence for candidate in candidates),
        "decision": "likely_guitar",
        "recommendation": recommendation,
        "recommendation_text": recommendation_text,
        "reasons": _top_reasons(candidates),
    }


def build_guitar_review_summary(report: GuitarDetectionReport) -> dict[str, Any]:
    """Hide low-scoring streams and group program fragments for product review."""

    likely = [
        candidate
        for candidate in report.candidates
        if candidate.decision == "likely_guitar"
    ]
    grouped: dict[tuple[int, int], list[GuitarStreamCandidate]] = defaultdict(list)
    for candidate in likely:
        grouped[(candidate.stream.source_track_index, candidate.stream.channel)].append(
            candidate
        )
    summaries = [_group_summary(items) for items in grouped.values()]
    summaries.sort(
        key=lambda item: (item["guitar_probability"], item["note_count"]),
        reverse=True,
    )
    possible_count = sum(
        candidate.decision == "possible_guitar" for candidate in report.candidates
    )
    unlikely_count = sum(
        candidate.decision == "unlikely_guitar" for candidate in report.candidates
    )
    return {
        "policy_version": SELECTION_POLICY_VERSION,
        "total_stream_count": report.stream_count,
        "guitar_part_count": len(summaries),
        "selected_stream_count": len(likely),
        "filtered_count": possible_count + unlikely_count,
        "possible_count": possible_count,
        "unlikely_count": unlikely_count,
        "recommended_stream_ids": [
            stream_id
            for summary in summaries
            for stream_id in summary["stream_ids"]
        ],
        "candidates": summaries,
    }
