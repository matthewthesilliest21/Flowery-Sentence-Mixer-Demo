from dataclasses import dataclass, asdict, field

@dataclass
class Fragment:
    kind: str
    text: str
    source: str
    start: float
    end: float
    confidence: float = 1.0
    phones: tuple[str, ...] = ()
    left_context: str = ""
    right_context: str = ""

    @property
    def duration(self):
        return max(0.0, self.end - self.start)

    def to_dict(self):
        d = asdict(self)
        d["phones"] = list(self.phones)
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(d["kind"], d["text"], d["source"], float(d.get("start", 0)),
                   float(d.get("end", 0)), float(d.get("confidence", 1)),
                   tuple(d.get("phones", [])), d.get("left_context", ""), d.get("right_context", ""))

@dataclass
class PlanStep:
    target_text: str
    fragment: Fragment | None
    score: float
    reason: str
    fragments: list[Fragment] = field(default_factory=list)

    @property
    def audio_fragments(self):
        if self.fragments:
            return self.fragments
        return [self.fragment] if self.fragment is not None else []

@dataclass
class Plan:
    target: str
    steps: list[PlanStep]
    total_score: float
    notes: list[str]
