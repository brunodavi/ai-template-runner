from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEmbedder:
    """The embeddings endpoint behind [memory], like a [provider] for vectors."""

    base_url: str
    model: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryCollection:
    """One named [memory.<name>] table: what to index and what to search for.

    Defaults mirror the commonly used RAG parameters; [memory] settings act
    as defaults that each collection may override per key.
    """

    name: str
    query: str = '{question}'
    source: str = ''
    db: str = ''
    chunk_size: int = 1024
    chunk_overlap: int = 128
    batch_size: int = 16
    top_k: int = 4
    max_chars: int = 2048
    min_score: float = 0.0


@dataclass
class Memory:
    """The promoted [memory] state: embedder plus fully-merged collections."""

    embedder: MemoryEmbedder
    collections: dict[str, MemoryCollection]
    sessions: dict = field(default_factory=dict)
