from dataclasses import asdict, dataclass, field


@dataclass(frozen=True, slots=True)
class HarmonyDecision:
    note_indices: tuple[int, ...]
    start_beat: float
    symbol: str
    root_pitch_class: int
    quality: str
    confidence: float
    reason: str


@dataclass(slots=True)
class HarmonyPlan:
    track_index: int
    track_name: str
    decisions: list[HarmonyDecision] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
