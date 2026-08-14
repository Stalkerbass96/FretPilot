"""Read-only AI rewrite advisory orchestration."""

from __future__ import annotations

from fretpilot.ai.context import build_shadow_rewrite_request
from fretpilot.ai.models import ShadowRewriteReport
from fretpilot.ai.providers.base import RewriteAdvisor
from fretpilot.ai.validation import validate_rewrite_proposal
from fretpilot.detection.models import InstrumentStream
from fretpilot.midi.models import NormalizedTimeline
from fretpilot.rewrite import rewrite_instrument_stream


def generate_shadow_rewrite_report(
    timeline: NormalizedTimeline,
    stream: InstrumentStream,
    provider: RewriteAdvisor,
    *,
    midi_fidelity: float,
    max_fret: int = 24,
    max_context_notes: int = 256,
) -> ShadowRewriteReport:
    """Request suggestions, validate them, and deliberately apply nothing."""

    baseline = rewrite_instrument_stream(
        stream,
        midi_fidelity=midi_fidelity,
        max_fret=max_fret,
        ticks_per_beat=timeline.ticks_per_beat,
    )
    request = build_shadow_rewrite_request(
        timeline,
        stream,
        baseline,
        max_context_notes=max_context_notes,
    )
    payload = provider.propose_rewrite(request)
    summary, accepted, rejected = validate_rewrite_proposal(
        request,
        payload,
        max_fret=max_fret,
    )
    return ShadowRewriteReport(
        request=request,
        provider=provider.identity,
        summary=summary,
        accepted_decisions=accepted,
        rejected_decisions=rejected,
    )
