from dataclasses import dataclass, field


@dataclass
class Provider:
    base_url: str

    model: str

    temperature: float = None
    top_p: float = None
    top_k: float = None

    max_tokens: int = None
    seed: int = None

    stop: list[str] = field(default_factory=list)

