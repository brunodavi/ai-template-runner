"""The [memory] table: template-local RAG backed by notes files and embeddings.

The template declares an embeddings endpoint ([memory] base_url/model, like
[provider]) and one named collection per table ([memory.notes]), each with a
query, a data source and retrieval parameters. Retrieval is lazy behind the
{memory.<name>} placeholders: the notes are chunked (paragraph-preserving),
embedded through the OpenAI-style /v1/embeddings endpoint and cached in a
sqlite3 index gated by a fingerprint of the sources plus the chunking/model
parameters, so the index rebuilds itself only when the notes or the setup
change.
"""

from glob import glob
from array import array
from hashlib import sha256
from json import dumps as json_dumps
import math
from pathlib import Path
import re
import sqlite3

from . import providers
from .output import Smart
from .models.memory import Memory, MemoryCollection, MemoryEmbedder

CHUNK_JOIN = '\n'
CONTEXT_JOIN = '\n\n'


def chunk_text(
        text: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 128,
    ) -> list[str]:
    """Split text into chunks of at most chunk_size characters.

    Paragraphs (blank-line separated) stay whole whenever they fit in a
    chunk; oversized pieces are cut with a sliding window whose stride is
    chunk_size - chunk_overlap, so the cut carries `chunk_overlap` shared
    characters between consecutive windows. Packed pieces are joined by a
    single newline and each chunk is stripped.
    """
    if chunk_size <= 0:
        raise ValueError('[memory] chunk_size must be a positive integer')

    if chunk_overlap >= chunk_size:
        raise ValueError('[memory] chunk_overlap must be smaller than chunk_size')

    step = chunk_size - chunk_overlap
    pieces = []
    for paragraph in re.split(r'\n\s*\n', text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if len(paragraph) <= chunk_size:
            pieces.append(paragraph)
        else:
            pieces.extend(
                paragraph[index:index + chunk_size]
                for index in range(0, len(paragraph), step)
            )

    chunks = []
    buffer = ''
    for piece in pieces:
        if buffer and len(buffer) + 1 + len(piece) > chunk_size:
            chunks.append(buffer)
            buffer = ''
        buffer = buffer + CHUNK_JOIN + piece if buffer else piece
    if buffer:
        chunks.append(buffer)

    return chunks


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity with the zero-vector convention of 0.0."""
    magnitude_a = math.sqrt(math.fsum(value * value for value in a))
    magnitude_b = math.sqrt(math.fsum(value * value for value in b))

    if not magnitude_a or not magnitude_b:
        return 0.0

    return math.fsum(
        value_a * value_b for value_a, value_b in zip(a, b)
    ) / (magnitude_a * magnitude_b)


def pack_vector(vector: list[float]) -> bytes:
    """Compact float32 encoding for the embeddings stored in the index."""
    return array('f', vector).tobytes()


def unpack_vector(blob: bytes) -> list[float]:
    values = array('f')
    values.frombytes(blob)
    return values.tolist()


def fingerprint(paths: list[Path], params: dict) -> str:
    """Hash of the sources and of the settings that shape the index.

    Sorted file names plus their bytes, then the canonical JSON of the
    params: any change to the notes or to the chunking/model setup flips
    the fingerprint and triggers a rebuild.
    """
    digest = sha256()

    for path in sorted(paths, key=str):
        digest.update(str(path).encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')

    digest.update(json_dumps(params, sort_keys=True, default=str).encode())

    return digest.hexdigest()


def fingerprint_params(collection: MemoryCollection, embedder: MemoryEmbedder) -> dict:
    """The parameters that decide whether the index must be rebuilt.

    Retrieval-only settings (top_k, min_score, max_chars, batch_size) are
    deliberately absent: they do not require re-embedding anything.
    """
    return {
        'model': embedder.model,
        'extras': embedder.extras,
        'chunk_size': collection.chunk_size,
        'chunk_overlap': collection.chunk_overlap,
    }


class MemoryStore:
    """sqlite3 index of chunk texts and their embeddings.

    matches() reads the stored fingerprint without creating the file;
    reset() unlinks first so a corrupted database cannot block the rebuild;
    rows keep their float32 vectors as blobs.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self._connection = None

    def _connect(self):
        if self._connection is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.path)
        return self._connection

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def matches(self, fingerprint: str) -> bool:
        if not self.path.is_file():
            return False

        try:
            row = self._connect().execute(
                'SELECT value FROM meta WHERE key = ?',
                ('fingerprint',),
            ).fetchone()
        except sqlite3.DatabaseError:
            return False

        return bool(row) and row[0] == fingerprint

    def reset(self, fingerprint: str) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

        self.path.unlink(missing_ok=True)

        connection = self._connect()
        connection.executescript('''
            DROP TABLE IF EXISTS meta;
            DROP TABLE IF EXISTS chunks;
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE chunks (source TEXT, idx INT, text TEXT, embedding BLOB);
        ''')
        connection.execute(
            'INSERT INTO meta (key, value) VALUES (?, ?)',
            ('fingerprint', fingerprint),
        )
        connection.commit()

    def insert(self, rows: list[tuple[str, int, str, list[float]]]) -> None:
        self._connect().executemany(
            'INSERT INTO chunks (source, idx, text, embedding) VALUES (?, ?, ?, ?)',
            [
                (source, idx, text, pack_vector(vector))
                for source, idx, text, vector in rows
            ],
        )
        self._connect().commit()

    def all(self) -> list[tuple[str, int, str, list[float]]]:
        rows = self._connect().execute(
            'SELECT source, idx, text, embedding FROM chunks ORDER BY source, idx'
        ).fetchall()

        return [
            (source, idx, text, unpack_vector(blob))
            for source, idx, text, blob in rows
        ]


SETTING_KEYS = (
    'source',
    'db',
    'query',
    'chunk_size',
    'chunk_overlap',
    'batch_size',
    'top_k',
    'max_chars',
    'min_score',
)

MEMORY_KEYS = set(SETTING_KEYS) | {'base_url', 'model', 'extras'}

INTEGER_KEYS = (
    'chunk_size',
    'chunk_overlap',
    'batch_size',
    'top_k',
    'max_chars',
)


def build_memory(raw) -> Memory | None:
    """Promote the parsed [memory] table into a Memory, validating as we go.

    Any dict value other than [memory.extras] is a collection table;
    [memory] settings act as defaults that every collection may override.
    Returns None when the template has no [memory] table at all.
    """
    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise ValueError('[memory] must be a table')

    embedder = MemoryEmbedder(
        base_url=raw.get('base_url') or '',
        model=raw.get('model') or '',
    )
    extras = raw.get('extras')

    if extras is not None and not isinstance(extras, dict):
        raise ValueError('[memory] extras must be a table')

    embedder.extras = dict(extras or {})

    if not embedder.base_url or not embedder.model:
        raise ValueError(
            "Memory requires 'base_url' and 'model', like [provider] "
            '(base_url is the full /v1/embeddings endpoint)'
        )

    # settings are scalars; every other dict value is a collection table
    collections = {}
    unknown = []
    for key, value in raw.items():
        if key in MEMORY_KEYS:
            if isinstance(value, dict) and key != 'extras':
                raise ValueError(
                    f'[memory.{key}] is a setting name; collection tables '
                    'cannot use it'
                )
            continue

        if isinstance(value, dict):
            collections[key] = value
        else:
            unknown.append(key)

    if unknown:
        raise ValueError(f'[memory] unknown key(s): {sorted(unknown)}')

    defaults = {key: raw[key] for key in SETTING_KEYS if key in raw}

    for name, table in collections.items():
        unknown = set(table) - set(SETTING_KEYS)
        if unknown:
            raise ValueError(
                f'[memory.{name}] unknown key(s): {sorted(unknown)}'
            )

        merged = {key: defaults[key] for key in SETTING_KEYS if key in defaults}
        merged.update(table)
        _validate_collection(name, merged)
        collections[name] = MemoryCollection(name=name, **merged)

    if not collections:
        raise ValueError(
            '[memory] declares no collection; add one like [memory.notes]'
        )

    return Memory(embedder=embedder, collections=collections)


def _validate_collection(name: str, values: dict) -> None:
    """Type-check the scalar settings of one collection, per table level."""
    for key in INTEGER_KEYS:
        if key in values:
            value = values[key]
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(
                    f'[memory.{name}] {key} must be a positive integer, got {value!r}'
                )

    if 'min_score' in values:
        value = values['min_score']
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f'[memory.{name}] min_score must be a number, got {value!r}'
            )

    for key in ('query', 'source', 'db'):
        if key in values and not isinstance(values[key], str):
            raise ValueError(
                f'[memory.{name}] {key} must be a string, got {values[key]!r}'
            )

    if values.get('chunk_overlap', 0) >= values.get('chunk_size', 1):
        raise ValueError(
            f'[memory.{name}] chunk_overlap must be smaller than chunk_size'
        )


def resolve_sources(
        collection: MemoryCollection,
        template_path: Path,
    ) -> list[Path]:
    """Resolve the collection sources, relative to the template file.

    A literal existing path resolves directly; anything with glob
    characters matches recursively relative to the template directory.
    Missing data must fail at load time, before any tokens are spent.
    """
    root = Path(template_path).parent
    pattern = collection.source

    if not pattern:
        raise ValueError(
            f'[memory.{collection.name}] needs a source '
            '(add source = "notes/notes.md")'
        )

    base = root / pattern

    if base.is_file():
        sources = [base]
    elif any(char in pattern for char in '*?['):
        sources = [Path(match) for match in glob(str(base), recursive=True)]
    else:
        sources = []

    if not sources:
        raise ValueError(
            f'[memory.{collection.name}] source not found: {pattern}'
        )

    return [source.resolve() for source in sources]


def resolve_db(
        collection: MemoryCollection,
        sources: list[Path],
        template_path: Path,
    ) -> Path:
    """Locate the collection index: explicit db, or next to the first source."""
    if collection.db:
        db = Path(template_path).parent / collection.db
    else:
        db = sources[0].with_suffix('.db')

    db = db.resolve()
    db.parent.mkdir(parents=True, exist_ok=True)

    return db


def embed_texts(
        embedder: MemoryEmbedder,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
    """Embed every text through the OpenAI-style /v1/embeddings endpoint."""
    vectors = []

    for start in range(0, len(texts), max(1, batch_size)):
        batch = texts[start:start + batch_size]
        response = providers.post_json(
            embedder.base_url,
            {
                'model': embedder.model,
                'input': batch,
                **embedder.extras,
            },
        )

        data = response.get('data') if isinstance(response, dict) else None

        if not isinstance(data, list) or len(data) != len(batch):
            found = len(data) if isinstance(data, list) else 'no data'
            raise ValueError(
                'memory embeddings response does not match the input: '
                f'expected {len(batch)} embedding(s), got {found}'
            )

        vectors.extend(list(item['embedding']) for item in data)

    return vectors


class MemorySession:
    """Lazy retriever behind {memory.<name>} placeholders, cached per run.

    Built once per template run by session(); the collection query is
    interpolated with the same slots the prompts get ({question}, {0},
    {1}...) before the embedding request, and results are Smart values so
    the :spec transforms and [slice] work as anywhere else.
    """

    def __init__(self, memory: Memory, question, args, template_path):
        self._memory = memory
        self._question = question
        self._args = list(args or [])
        self._template_path = (
            Path(template_path).resolve() if template_path is not None else None
        )
        self._cache: dict[str, Smart] = {}

    def __getattr__(self, name: str) -> Smart:
        if name.startswith('_'):
            raise AttributeError(name)

        if name not in self._cache:
            collection = self._memory.collections.get(name)
            if collection is None:
                available = ', '.join(self._memory.collections)
                raise ValueError(
                    f'usage error: unknown memory collection "{name}" '
                    f'(available: {available})'
                )

            self._cache[name] = Smart(self._retrieve(collection))

        return self._cache[name]

    def _retrieve(self, collection: MemoryCollection) -> str:
        sources = resolve_sources(collection, self._template_path)
        store = MemoryStore(resolve_db(collection, sources, self._template_path))
        reference = fingerprint(
            sources,
            fingerprint_params(collection, self._memory.embedder),
        )

        try:
            if not store.matches(reference):
                rows = []
                for source in sources:
                    for idx, piece in enumerate(
                        chunk_text(
                            source.read_text(),
                            collection.chunk_size,
                            collection.chunk_overlap,
                        )
                    ):
                        rows.append((str(source), idx, piece))

                vectors = embed_texts(
                    self._memory.embedder,
                    [text for _, _, text in rows],
                    collection.batch_size,
                )

                store.reset(reference)
                store.insert([
                    (source, idx, text, vector)
                    for (source, idx, text), vector in zip(rows, vectors)
                ])

            query_text = self._interpolate_query(collection)
            query_vector = embed_texts(self._memory.embedder, [query_text])[0]

            return self._search(store, query_vector, collection)
        finally:
            store.close()

    def _search(
            self,
            store: MemoryStore,
            query_vector: list[float],
            collection: MemoryCollection,
        ) -> str:
        scored = []
        for source, idx, text, vector in store.all():
            score = cosine(query_vector, vector)
            if score >= collection.min_score:
                scored.append((score, source, idx, text))

        scored.sort(key=lambda row: (-row[0], row[1], row[2]))

        parts = []
        total = 0
        for score, source, idx, text in scored[:collection.top_k]:
            separation = len(CONTEXT_JOIN) if parts else 0
            if parts and total + separation + len(text) > collection.max_chars:
                break

            parts.append(text)
            total += separation + len(text)

        return CONTEXT_JOIN.join(parts)

    def _interpolate_query(self, collection: MemoryCollection) -> str:
        path_value = str(self._template_path)
        slots = (
            ([self._question] if self._question is not None else [])
            + self._args
        )

        try:
            return collection.query.format(
                Smart(path_value),
                *[Smart(value) for value in slots],
                question=(
                    Smart(self._question)
                    if isinstance(self._question, str)
                    else self._question
                ),
            ).strip()
        except KeyError as error:
            raise ValueError(
                'usage error: unknown placeholder '
                f'"{error.args[0]}" in [memory.{collection.name}] query '
                '(available: {question}, {0}, {1}, {2}...)'
            ) from None
        except IndexError as error:
            raise ValueError(
                f'usage error: not enough args for [memory.{collection.name}] query'
            ) from None
        except ValueError as error:
            if 'cannot switch from' in str(error):
                raise ValueError(
                    'usage error: {} cannot be mixed with {0}-style numbered '
                    'slots (use {0}, {1}, {2}...)'
                ) from None
            raise


def session(memory: Memory, question, args, template_path) -> MemorySession:
    """One MemorySession per template run (same slots share the cache)."""
    key = (
        question,
        tuple(args or []),
        str(template_path) if template_path is not None else None,
    )

    if key not in memory.sessions:
        memory.sessions[key] = MemorySession(memory, question, args, template_path)

    return memory.sessions[key]
