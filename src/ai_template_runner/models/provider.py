from dataclasses import dataclass, field


@dataclass
class Provider:
    base_url: str

    model: str

    temperature: float | None = None
    top_p: float | None = None
    top_k: float | None = None

    max_tokens: int | None = None
    seed: int | None = None

    stop: list[str] = field(default_factory=list)

