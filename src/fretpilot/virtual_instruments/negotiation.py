"""Provider-neutral capability negotiation for virtual guitar instruments.

Negotiation converts canonical musical intent names into an explicit target
support decision plus the profile's generic ``ControlAction`` declarations. It
does not emit MIDI and it does not mutate Guitar IR or PerformancePlan data.
"""

from __future__ import annotations

from dataclasses import dataclass

from fretpilot.virtual_instruments.models import (
    ControlAction,
    VirtualGuitarInstrumentProfile,
)


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    requested_intent: str
    resolved_intent: str | None
    support: str
    actions: tuple[ControlAction, ...] = ()
    fallback_chain: tuple[str, ...] = ()
    notes: str = ""

    @property
    def supported(self) -> bool:
        return self.support in {"native", "approximated"}


def negotiate_intent(
    profile: VirtualGuitarInstrumentProfile,
    intent: str,
) -> CapabilityResolution:
    """Resolve one canonical intent against one approved target profile.

    Missing declarations and explicit ``unsupported`` capabilities are both
    returned as explicit unsupported results. ``requires_fallback`` follows the
    declared fallback chain deterministically; a successfully resolved fallback
    is reported as ``approximated`` so callers cannot mistake it for native
    realization of the original intent.
    """

    chain: list[str] = []
    current = intent

    while True:
        if current in chain:
            cycle = " -> ".join([*chain, current])
            raise ValueError(
                f"Capability fallback cycle in profile {profile.profile_id!r}: {cycle}."
            )
        chain.append(current)
        capability = profile.capability(current)

        if capability is None:
            return CapabilityResolution(
                requested_intent=intent,
                resolved_intent=None,
                support="unsupported",
                actions=(),
                fallback_chain=tuple(chain),
                notes=(
                    f"Profile {profile.profile_id!r} declares no capability for "
                    f"intent {current!r}."
                ),
            )

        if capability.support == "unsupported":
            return CapabilityResolution(
                requested_intent=intent,
                resolved_intent=current,
                support="unsupported",
                actions=(),
                fallback_chain=tuple(chain),
                notes=capability.notes,
            )

        if capability.support == "requires_fallback":
            assert capability.fallback_intent is not None
            current = capability.fallback_intent
            continue

        effective_support = capability.support
        if len(chain) > 1:
            effective_support = "approximated"
        return CapabilityResolution(
            requested_intent=intent,
            resolved_intent=current,
            support=effective_support,
            actions=capability.actions,
            fallback_chain=tuple(chain),
            notes=capability.notes,
        )


def negotiate_intents(
    profile: VirtualGuitarInstrumentProfile,
    intents: list[str] | tuple[str, ...],
) -> tuple[CapabilityResolution, ...]:
    """Resolve intents in caller order without deduplicating musical events."""

    return tuple(negotiate_intent(profile, intent) for intent in intents)
