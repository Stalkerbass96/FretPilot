"""Curated public sources used to distill reusable guitar-playing knowledge.

Only factual summaries and derived priors belong in runtime knowledge. Do not
copy or redistribute source tablature/examples from these references.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


RESEARCH_SOURCE_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    source_id: str
    title: str
    url: str
    source_kind: str
    published_year: int | None
    authority: str
    usage_policy: str = "fact_summary_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SOURCES: tuple[KnowledgeSource, ...] = (
    KnowledgeSource(
        "bontempi-rich-tab-2024",
        "From MIDI to Rich Tablatures: an Automatic Generative System incorporating Lead Guitarists' Fingering and Stylistic choices",
        "https://arxiv.org/abs/2407.09052",
        "research_paper",
        2024,
        "research",
    ),
    KnowledgeSource(
        "dhooge-chord-context-2024",
        "Guitar Chord Diagram Suggestion for Western Popular Music",
        "https://arxiv.org/abs/2407.14260",
        "research_paper",
        2024,
        "research",
    ),
    KnowledgeSource(
        "fretboardflow-2025",
        "FretboardFlow: A Dual-Model Approach to Optimize Chord Voicings on the Guitar Fretboard",
        "https://ismir2025program.ismir.net/poster_266.html",
        "conference_research",
        2025,
        "ISMIR research",
    ),
    KnowledgeSource(
        "kunjara-drop2-2025",
        "Drop 2 Voicing for Guitar",
        "https://so06.tci-thaijo.org/index.php/rmj/article/view/278341",
        "journal_article",
        2025,
        "academic journal",
    ),
    KnowledgeSource(
        "fender-blues-scale",
        "How to Play Blues Scales on Guitar",
        "https://www.fender.com/articles/scales/blues-guitar-scale",
        "manufacturer_education",
        None,
        "Fender education",
    ),
    KnowledgeSource(
        "fender-palm-mute",
        "3 Keys to Ace Your Palm Muting",
        "https://www.fender.com/articles/techniques/3-keys-to-ace-your-palm-muting",
        "manufacturer_education",
        None,
        "Fender education",
    ),
    KnowledgeSource(
        "fender-picking-styles",
        "Chicken, Tremolo, Sweep. Pick Your Picking Style.",
        "https://www.fender.com/articles/techniques/what-type-of-picker-are-you",
        "manufacturer_education",
        None,
        "Fender education",
    ),
    KnowledgeSource(
        "fender-travis-picking",
        "Learn the Travis Picking Guitar Technique",
        "https://www.fender.com/articles/techniques/travis-picking-on-guitar",
        "manufacturer_education",
        None,
        "Fender education",
    ),
    KnowledgeSource(
        "fender-rnb-soul",
        "Learn to Play R&B / Soul Songs with Fender Play",
        "https://www.fender.com/articles/songs/r-and-b-soul-path",
        "manufacturer_education",
        None,
        "Fender education",
    ),
)


_BY_ID = {item.source_id: item for item in SOURCES}


def get_source(source_id: str) -> KnowledgeSource | None:
    return _BY_ID.get(source_id)


def source_snapshot() -> dict[str, Any]:
    return {
        "version": RESEARCH_SOURCE_VERSION,
        "sources": [item.to_dict() for item in SOURCES],
    }
