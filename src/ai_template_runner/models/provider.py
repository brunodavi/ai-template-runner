from dataclasses import dataclass, field
from typing import Any


@dataclass
class Provider:
    base_url: str
    model: str

    # Sampling
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None

    # Output
    max_tokens: int | None = None
    stop: list[str] = field(default_factory=list)

    # Reproducibility
    seed: int | None = None

    # Repetition control
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    repeat_penalty: float | None = None

    # Less common or provider-specific options
    extras: dict[str, Any] = field(default_factory=dict)
