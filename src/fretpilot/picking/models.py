from dataclasses import asdict, dataclass, field

@dataclass(frozen=True, slots=True)
class PickingDecision:
    note_indices: tuple[int, ...]
    start_beat: float
    motion: str
    direction: str
    confidence: float
    reason: str
    technique: str | None = None

@dataclass(slots=True)
class PickingPlan:
    track_index: int
    track_name: str
    decisions: list[PickingDecision] = field(default_factory=list)
    def to_dict(self):
        return asdict(self)
