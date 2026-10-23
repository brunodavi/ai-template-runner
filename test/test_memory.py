from unittest import TestCase
from unittest.mock import patch
from tempfile import TemporaryDirectory
from pathlib import Path

from src.ai_template_runner.memory import (
    build_memory,
    chunk_text,
    cosine,
    embed_texts,
    fingerprint,
    pack_vector,
    resolve_db,
    resolve_sources,
    session,
    unpack_vector,
)
from src.ai_template_runner.memory import MemoryStore
from src.ai_template_runner.models.memory import MemoryCollection, MemoryEmbedder
from src.ai_template_runner.processor import (
    process_prompt,
    process_system_prompt,
    process_template,
)


NOTES_DIR = 'notes'
NOTES_FILE = f'{NOTES_DIR}/task-notes.md'
PARAGRAPH_ONE = 'ARTICLE segment speaks about the first thing.'
PARAGRAPH_TWO = 'BRAVO segment speaks about the second thing.'
NOTES_TEXT = PARAGRAPH_ONE + '\n\n' + PARAGRAPH_TWO


def make_embedder(model: str = 'emb-test') -> MemoryEmbedder:
    return MemoryEmbedder(
        base_url='http://localhost:8081/v1/embeddings',
        model=model,
    )


def vectors_for_text(text: str) -> list[float]:
    """Deterministic embeddings: ARTICLE chunks and BRAVO chunks are orthogonal."""
    if 'BRAVO' in text:
        return [0.0, 1.0]

    if 'ARTICLE' in text:
        return [1.0, 0.0]

    if 'CHARLIE' in text:
        return [0.3, 0.7]

    raise ValueError(f'unexpected embedding request: {text!r}')


def fake_post_json(url, payload):
    """OpenAI-ish dispatcher: 'input' means embeddings, otherwise chat."""
    if 'input' in payload:
        return {
            'data': [
                {'embedding': vectors_for_text(text)}
                for text in payload['input']
            ]
        }

    return {'choices': [{'message': {'content': 'ANSWER'}}]}


class TestChunkText(TestCase):
    def test_empty_text_makes_no_chunks(self):
        self.assertEqual(chunk_text('', 100, 10), [])
        self.assertEqual(chunk_text('  \n\n  ', 100, 10), [])

    def test_short_text_makes_one_chunk(self):
        self.assertEqual(chunk_text('hello world', 100, 10), ['hello world'])

    def test_each_chunk_is_stripped(self):
        self.assertEqual(chunk_text('  pad  ', 100, 10), ['pad'])

    def test_chunks_slide_with_overlap(self):
        # step = chunk_size - chunk_overlap = 3
        self.assertEqual(
            chunk_text('abcdefghij', 4, 1),
            ['abcd', 'defg', 'ghij', 'j'],
        )

    def test_overlap_is_shared_between_chunks(self):
        text = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        chunks = chunk_text(text, 10, 2)

        self.assertEqual(chunks[0][8:10], chunks[1][0:2])
        self.assertEqual(chunks[1][8:10], chunks[2][0:2])

    def test_paragraphs_stay_whole_when_they_fit(self):
        text = PARAGRAPH_ONE + '\n\n' + PARAGRAPH_TWO

        self.assertEqual(chunk_text(text, 64, 8), [PARAGRAPH_ONE, PARAGRAPH_TWO])

    def test_paragraphs_pack_together_when_they_share_a_chunk(self):
        text = PARAGRAPH_ONE + '\n\n' + PARAGRAPH_TWO

        self.assertEqual(chunk_text(text, 200, 10), [PARAGRAPH_ONE + '\n' + PARAGRAPH_TWO])

    def test_paragraph_is_not_cut_when_length_matches_chunk_size(self):
        text = 'x' * 40

        self.assertEqual(chunk_text(text, 40, 10), [text])

    def test_oversized_paragraph_is_windowed_with_overlap(self):
        text = 'abcdefghij' * 10  # 100 chars
        chunks = chunk_text(text, 40, 10)

        # each window is at most chunk_size
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 40)

        # the sliding stride is chunk_size - chunk_overlap
        for first, second in zip(chunks, chunks[1:]):
            self.assertIn(first[-10:], second)

    def test_overlap_larger_than_chunk_size_is_rejected(self):
        with self.assertRaises(ValueError) as err:
            chunk_text('some text', 10, 10)

        self.assertIn('chunk_overlap', str(err.exception))

    def test_default_parameters_are_documented(self):
        text = 'x' * 2048

        self.assertEqual(chunk_text(text, 1024, 128), chunk_text(text))


class TestCosine(TestCase):
    def test_identical_vectors_score_one(self):
        self.assertAlmostEqual(cosine([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)

    def test_orthogonal_vectors_score_zero(self):
        self.assertAlmostEqual(cosine([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_opposite_vectors_score_minus_one(self):
        self.assertAlmostEqual(cosine([1.0, 0.0], [-1.0, 0.0]), -1.0)

    def test_zero_vector_scores_zero(self):
        self.assertAlmostEqual(cosine([0.0, 0.0], [1.0, 2.0]), 0.0)
        self.assertAlmostEqual(cosine([1.0, 2.0], [0.0, 0.0]), 0.0)

    def test_scale_does_not_change_the_score(self):
        self.assertAlmostEqual(cosine([1.0, 2.0], [2.0, 4.0]), 1.0)


class TestFingerprint(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def test_same_sources_and_params_make_same_fingerprint(self):
        alpha = self.write('notes/alpha.md', NOTES_TEXT)
        bravo = self.write('notes/bravo.md', NOTES_TEXT)
        params = {'model': 'emb-test', 'chunk_size': 1024}

        self.assertEqual(
            fingerprint([alpha, bravo], params),
            fingerprint([alpha, bravo], params),
        )

    def test_fingerprint_does_not_depend_on_path_order(self):
        alpha = self.write('notes/alpha.md', 'alpha text')
        bravo = self.write('notes/bravo.md', 'bravo text')
        params = {'model': 'emb-test'}

        self.assertEqual(
            fingerprint([alpha, bravo], params),
            fingerprint([bravo, alpha], params),
        )

    def test_changed_source_changes_the_fingerprint(self):
        alpha = self.write('notes/alpha.md', 'alpha text')
        before = fingerprint([alpha], {'model': 'emb-test'})

        self.write('notes/alpha.md', 'alpha text edited')

        self.assertNotEqual(fingerprint([alpha], {'model': 'emb-test'}), before)

    def test_changed_params_change_the_fingerprint(self):
        alpha = self.write('notes/alpha.md', 'alpha text')

        self.assertNotEqual(
            fingerprint([alpha], {'model': 'emb-test'}),
            fingerprint([alpha], {'model': 'other-model'}),
        )
        self.assertNotEqual(
            fingerprint([alpha], {'model': 'emb-test', 'chunk_size': 1024}),
            fingerprint([alpha], {'model': 'emb-test', 'chunk_size': 512}),
        )

    def test_different_files_do_not_collide(self):
        alpha = self.write('notes/alpha.md', 'same content')
        bravo = self.write('notes/bravo.md', 'same content')

        self.assertNotEqual(
            fingerprint([alpha], {'model': 'emb-test'}),
            fingerprint([bravo], {'model': 'emb-test'}),
        )


class TestPackVector(TestCase):
    def test_round_trip(self):
        blob = pack_vector([0.5, -0.25, 0.125, 7.0])
        restored = unpack_vector(blob)

        self.assertEqual(len(restored), 4)
        for restored_value, original in zip(restored, [0.5, -0.25, 0.125, 7.0]):
            self.assertAlmostEqual(restored_value, original, delta=1e-6)

    def test_empty_vector_round_trip(self):
        self.assertEqual(unpack_vector(pack_vector([])), [])


class TestMemoryStore(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.store = MemoryStore(self.root / 'db' / 'memory.db')
        self.addCleanup(self.store.close)

    def test_fresh_store_reports_no_match_without_creating_the_file(self):
        self.assertFalse(self.store.matches('fingerprint-1'))
        self.assertFalse((self.root / 'db' / 'memory.db').exists())

    def test_reset_insert_and_all_round_trip(self):
        self.store.reset('fingerprint-1')
        self.store.insert([
            (NOTES_FILE, 0, PARAGRAPH_ONE, [0.5, 0.25]),
            (NOTES_FILE, 1, PARAGRAPH_TWO, [1.0, 0.0]),
        ])

        self.assertTrue(self.store.matches('fingerprint-1'))
        rows = self.store.all()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], NOTES_FILE)
        self.assertEqual(rows[0][1], 0)
        self.assertEqual(rows[0][2], PARAGRAPH_ONE)
        for restored, original in zip(rows[0][3], [0.5, 0.25]):
            self.assertAlmostEqual(restored, original, delta=1e-6)
        for restored, original in zip(rows[1][3], [1.0, 0.0]):
            self.assertAlmostEqual(restored, original, delta=1e-6)

    def test_all_is_ordered_by_source_and_idx(self):
        self.store.reset('fingerprint-1')
        self.store.insert([
            ('b.md', 0, 'bravo', [1.0]),
            ('a.md', 1, 'alpha two', [0.0]),
            ('a.md', 0, 'alpha one', [0.5]),
        ])

        rows = self.store.all()

        self.assertEqual([row[:3] for row in rows], [
            ('a.md', 0, 'alpha one'),
            ('a.md', 1, 'alpha two'),
            ('b.md', 0, 'bravo'),
        ])

    def test_reset_clears_rows_and_swaps_the_fingerprint(self):
        self.store.reset('fingerprint-1')
        self.store.insert([(NOTES_FILE, 0, PARAGRAPH_ONE, [0.5])])

        self.store.reset('fingerprint-2')

        self.assertTrue(self.store.matches('fingerprint-2'))
        self.assertFalse(self.store.matches('fingerprint-1'))
        self.assertEqual(self.store.all(), [])

    def test_corrupt_database_is_reported_as_no_match_and_is_recovered(self):
        path = self.root / 'db' / 'memory.db'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'corrupted, not sqlite')

        self.assertFalse(self.store.matches('fingerprint-1'))

        self.store.reset('fingerprint-1')

        self.assertTrue(self.store.matches('fingerprint-1'))


class TestEmbedTexts(TestCase):
    @patch('src.ai_template_runner.providers.post_json')
    def test_posts_openai_shaped_payload_to_the_embeddings_url(self, mock_post_json):
        mock_post_json.return_value = {'data': [
            {'embedding': [0.1, 0.2]},
            {'embedding': [0.3, 0.4]},
        ]}
        embedder = MemoryEmbedder(
            base_url='http://localhost:8081/v1/embeddings',
            model='emb-test',
            extras={'dimensions': 2},
        )

        vectors = embed_texts(embedder, ['alpha note', 'bravo note'])

        self.assertEqual(vectors, [[0.1, 0.2], [0.3, 0.4]])

        url, payload = mock_post_json.call_args.args
        self.assertEqual(url, 'http://localhost:8081/v1/embeddings')
        self.assertEqual(payload['model'], 'emb-test')
        self.assertEqual(payload['input'], ['alpha note', 'bravo note'])
        self.assertEqual(payload['dimensions'], 2)

    @patch('src.ai_template_runner.providers.post_json')
    def test_batches_texts_by_batch_size(self, mock_post_json):
        mock_post_json.side_effect = (
            lambda url, payload: {
                'data': [
                    {'embedding': [0.1, 0.2]} for _ in payload['input']
                ]
            }
        )

        embed_texts(make_embedder(), ['one', 'two', 'three'], batch_size=2)

        self.assertEqual(mock_post_json.call_count, 2)
        first_input = mock_post_json.call_args_list[0].args[1]['input']
        second_input = mock_post_json.call_args_list[1].args[1]['input']
        self.assertEqual(first_input, ['one', 'two'])
        self.assertEqual(second_input, ['three'])

    @patch('src.ai_template_runner.providers.post_json')
    def test_data_length_mismatch_is_a_value_error(self, mock_post_json):
        mock_post_json.return_value = {'data': [{'embedding': [0.1, 0.2]}]}

        with self.assertRaises(ValueError) as err:
            embed_texts(make_embedder(), ['one', 'two'])

        self.assertIn('embedding', str(err.exception))

    @patch('src.ai_template_runner.providers.post_json')
    def test_missing_data_is_a_value_error(self, mock_post_json):
        mock_post_json.return_value = {'unexpected': True}

        with self.assertRaises(ValueError) as err:
            embed_texts(make_embedder(), ['one'])

        self.assertIn('embedding', str(err.exception))


class TestBuildMemory(TestCase):
    def test_minimal_config_applies_the_documented_defaults(self):
        memory = build_memory({
            'base_url': 'http://localhost:8081/v1/embeddings',
            'model': 'emb-test',
            'notes': {},
        })

        self.assertEqual(memory.embedder.base_url, 'http://localhost:8081/v1/embeddings')
        self.assertEqual(memory.embedder.model, 'emb-test')
        self.assertEqual(memory.embedder.extras, {})

        collection = memory.collections['notes']
        self.assertEqual(collection.name, 'notes')
        self.assertEqual(collection.query, '{question}')
        self.assertEqual(collection.source, '')
        self.assertEqual(collection.db, '')
        self.assertEqual(collection.chunk_size, 1024)
        self.assertEqual(collection.chunk_overlap, 128)
        self.assertEqual(collection.batch_size, 16)
        self.assertEqual(collection.top_k, 4)
        self.assertEqual(collection.max_chars, 2048)
        self.assertEqual(collection.min_score, 0.0)

    def test_memory_settings_flow_into_the_collections(self):
        memory = build_memory({
            'base_url': 'http://localhost:8081/v1/embeddings',
            'model': 'emb-test',
            'source': NOTES_FILE,
            'query': 'wrong-query',
            'top_k': 2,
            'notes': {'query': 'find {question}'},
        })

        collection = memory.collections['notes']
        self.assertEqual(collection.source, NOTES_FILE)
        self.assertEqual(collection.query, 'find {question}')
        self.assertEqual(collection.top_k, 2)

    def test_collection_overrides_win_per_key(self):
        memory = build_memory({
            'base_url': 'http://localhost:8081/v1/embeddings',
            'model': 'emb-test',
            'source': NOTES_FILE,
            'chunk_size': 200,
            'a': {'chunk_size': 50, 'source': 'a-notes.md'},
            'b': {},
        })

        self.assertEqual(memory.collections['a'].chunk_size, 50)
        self.assertEqual(memory.collections['a'].source, 'a-notes.md')
        self.assertEqual(memory.collections['b'].chunk_size, 200)
        self.assertEqual(memory.collections['b'].source, NOTES_FILE)

    def test_base_url_and_model_are_required(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'model': 'emb-test',
                'notes': {},
            })

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))

        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'notes': {},
            })

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))

    def test_at_least_one_collection_is_required(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'model': 'emb-test',
            })

        self.assertIn('[memory.notes]', str(err.exception))

    def test_unknown_memory_key_is_rejected(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'model': 'emb-test',
                'chunk_sizes': 100,
                'notes': {},
            })

        self.assertIn('chunk_sizes', str(err.exception))

    def test_unknown_collection_key_is_rejected(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'model': 'emb-test',
                'notes': {'sourcee': 'notes/notes.md'},
            })

        self.assertIn('[memory.notes]', str(err.exception))
        self.assertIn('sourcee', str(err.exception))

    def test_scalar_parameters_are_type_checked(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'model': 'emb-test',
                'notes': {'chunk_size': 'big'},
            })

        self.assertIn('chunk_size', str(err.exception))

    def test_chunk_overlap_must_be_smaller_than_chunk_size(self):
        with self.assertRaises(ValueError) as err:
            build_memory({
                'base_url': 'http://localhost:8081/v1/embeddings',
                'model': 'emb-test',
                'notes': {'chunk_size': 100, 'chunk_overlap': 100},
            })

        self.assertIn('chunk_overlap', str(err.exception))

    def test_extras_are_kept_for_the_embeddings_payload(self):
        memory = build_memory({
            'base_url': 'http://localhost:8081/v1/embeddings',
            'model': 'emb-test',
            'extras': {'dimensions': 768},
            'notes': {},
        })

        self.assertEqual(memory.embedder.extras, {'dimensions': 768})


class TestMemoryResolution(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name: str, content: str = NOTES_TEXT) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def make_collection(self, **overrides) -> MemoryCollection:
        build = {
            'name': 'notes',
            'source': NOTES_FILE,
        }
        build.update(overrides)
        return MemoryCollection(**build)

    def test_literal_source_resolves_relative_to_the_template(self):
        path = self.write(NOTES_FILE)
        collection = self.make_collection()

        sources = resolve_sources(collection, self.root / 'template.md')

        self.assertEqual(sources, [path.resolve()])

    def test_glob_source_resolves_every_match_sorted(self):
        alpha = self.write(f'{NOTES_DIR}/alpha.md', 'alpha')
        bravo = self.write(f'{NOTES_DIR}/bravo.md', 'bravo')
        collection = self.make_collection(source=f'{NOTES_DIR}/*.md')

        sources = resolve_sources(collection, self.root / 'template.md')

        self.assertEqual(sources, [alpha.resolve(), bravo.resolve()])

    def test_glob_results_are_sorted_even_when_the_files_are_not(self):
        from unittest.mock import patch

        alpha = self.write(f'{NOTES_DIR}/alpha.md', 'alpha')
        bravo = self.write(f'{NOTES_DIR}/bravo.md', 'bravo')
        collection = self.make_collection(source=f'{NOTES_DIR}/*.md')

        # os.scandir does not guarantee order: simulate an unsorted match
        with patch(
            'src.ai_template_runner.memory.glob',
            return_value=[str(bravo), str(alpha)],
        ):
            sources = resolve_sources(collection, self.root / 'template.md')

        self.assertEqual(sources, [alpha.resolve(), bravo.resolve()])

    def test_missing_source_is_a_value_error(self):
        collection = self.make_collection(source='notes/missing.md')

        with self.assertRaises(ValueError) as err:
            resolve_sources(collection, self.root / 'template.md')

        self.assertIn('notes/missing.md', str(err.exception))

    def test_empty_glob_is_a_value_error(self):
        collection = self.make_collection(source=f'{NOTES_DIR}/nothing-*.md')

        with self.assertRaises(ValueError) as err:
            resolve_sources(collection, self.root / 'template.md')

        self.assertIn('nothing-*.md', str(err.exception))

    def test_empty_source_is_a_value_error(self):
        collection = self.make_collection(source='')

        with self.assertRaises(ValueError) as err:
            resolve_sources(collection, self.root / 'template.md')

        self.assertIn('source', str(err.exception))

    def test_db_defaults_next_to_the_first_source(self):
        path = self.write(NOTES_FILE)
        collection = self.make_collection()
        sources = resolve_sources(collection, self.root / 'template.md')

        db = resolve_db(collection, sources, self.root / 'template.md')

        self.assertEqual(db, path.resolve().with_suffix('.db'))

    def test_explicit_db_resolves_relative_to_the_template(self):
        self.write(NOTES_FILE)
        collection = self.make_collection(db='memory/notes.db')
        sources = resolve_sources(collection, self.root / 'template.md')

        db = resolve_db(collection, sources, self.root / 'template.md')

        self.assertEqual(db, (self.root / 'memory' / 'notes.db').resolve())


class TestProcessorMemory(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write_template(self, name: str, *lines: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('\n'.join(lines))
        return path

    def write_memory_template(self, name: str = 'memory.md', **collection) -> Path:
        self.root.joinpath(NOTES_DIR).mkdir(exist_ok=True)
        (self.root / NOTES_FILE).write_text(NOTES_TEXT)

        lines = [
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'base_url = "http://localhost:8081/v1/embeddings"',
            'model = "emb-test"',
            'source = "notes/task-notes.md"',
            'db = "memory-templates.db"',
        ]
        for key, value in collection.items():
            lines.append(f'{key} = {value!r}')
        lines += [
            '[memory.notes]',
            '[memory.other]',
            'query = "about {question}"',
            '```',
            '---',
            'Answer with the notes.',
            '---',
            'Notes: {memory.notes}',
            'Also: {memory.other}',
        ]

        return self.write_template(name, *lines)

    def test_template_with_memory_builds_the_collections(self):
        template = process_template(self.write_memory_template())

        self.assertEqual(list(template.memory.collections), ['notes', 'other'])
        self.assertEqual(
            template.memory.embedder.base_url,
            'http://localhost:8081/v1/embeddings',
        )
        self.assertEqual(template.memory.embedder.model, 'emb-test')
        self.assertEqual(template.memory.collections['other'].query, 'about {question}')

    def test_template_without_memory_is_none(self):
        template = process_template(self.write_template('plain.md',
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '```',
            'prompt',
        ))

        self.assertIsNone(template.memory)

    def test_memory_requires_base_url_and_model(self):
        path = self.write_template('broken.md',
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'model = "emb-test"',
            '[memory.notes]',
            '```',
            'prompt',
        )

        with self.assertRaises(ValueError) as err:
            process_template(path)

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))

    def test_memory_source_must_exist_at_load_time(self):
        path = self.write_template('ghost.md',
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'base_url = "http://localhost:8081/v1/embeddings"',
            'model = "emb-test"',
            'source = "notes/missing.md"',
            '[memory.notes]',
            '```',
            'prompt',
        )

        with self.assertRaises(ValueError) as err:
            process_template(path)

        self.assertIn('notes/missing.md', str(err.exception))

    def test_memory_glob_without_matches_fails_at_load_time(self):
        self.root.joinpath(NOTES_DIR).mkdir(exist_ok=True)
        path = self.write_template('clueless.md',
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'base_url = "http://localhost:8081/v1/embeddings"',
            'model = "emb-test"',
            'source = "notes/gone-*.md"',
            '[memory.notes]',
            '```',
            'prompt {memory.notes}',
        )

        with self.assertRaises(ValueError) as err:
            process_template(path)

        self.assertIn('notes/gone-*.md', str(err.exception))

    def test_child_inherits_memory_tables_through_extends(self):
        self.root.joinpath(NOTES_DIR).mkdir(exist_ok=True)
        (self.root / NOTES_FILE).write_text(NOTES_TEXT)
        self.write_template('base.md',
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'base_url = "http://localhost:8081/v1/embeddings"',
            'model = "emb-test"',
            'source = "notes/task-notes.md"',
            '[memory.notes]',
            'max_chars = 10',
            '```',
            'base prompt',
        )
        child = self.write_template('child.md',
            '```toml',
            'extends = "base.md"',
            '[memory.notes]',
            'top_k = 1',
            '```',
            'child prompt',
        )

        template = process_template(child)

        collection = template.memory.collections['notes']
        self.assertEqual(collection.source, NOTES_FILE)
        self.assertEqual(collection.max_chars, 10)
        self.assertEqual(collection.top_k, 1)


class TestMemorySession(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def make_memory(self, db: str = 'memory/memory.db', **overrides):
        raw = {
            'base_url': 'http://localhost:8081/v1/embeddings',
            'model': 'emb-test',
            'source': NOTES_FILE,
            'db': db,
            'chunk_size': 64,
            'chunk_overlap': 8,
            'query': '{question}',
            'notes': {},
        }
        raw.update(overrides)
        return build_memory(raw)

    def retrieve(self, memory, question: str, args=None):
        memory_session = session(memory, question, args or [], self.root / 'template.md')
        return memory_session.notes

    @patch('src.ai_template_runner.providers.post_json')
    def test_retrieval_ranks_the_relevant_chunks_first(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        text = str(self.retrieve(self.make_memory(), 'BRAVO please'))

        self.assertIn('BRAVO', text)
        self.assertIn('ARTICLE', text)
        self.assertLess(text.index('BRAVO'), text.index('ARTICLE'))

    @patch('src.ai_template_runner.providers.post_json')
    def test_query_embeds_the_interpolated_question(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)
        memory = self.make_memory()

        self.retrieve(memory, 'BRAVO please', ['and', 'more'])

        inputs = [
            call.args[1]['input']
            for call in mock_post_json.call_args_list
        ]
        self.assertIn('BRAVO please', inputs[-1])

    @patch('src.ai_template_runner.providers.post_json')
    def test_chunks_are_embedded_in_a_single_batch_by_default(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        self.retrieve(self.make_memory(), 'BRAVO please')

        inputs = [
            call.args[1]['input']
            for call in mock_post_json.call_args_list
        ]
        self.assertEqual(len(inputs), 2)          # one for the chunks, one for the query
        self.assertEqual(len(inputs[0]), 2)       # both chunks in one batch

    @patch('src.ai_template_runner.providers.post_json')
    def test_retrieval_is_cached_within_the_session(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        memory_session = session(self.make_memory(), 'BRAVO please', [], self.root / 'template.md')
        first = memory_session.notes
        second = memory_session.notes

        self.assertEqual(first, second)
        self.assertEqual(mock_post_json.call_count, 2)  # chunks + query, no re-run

    @patch('src.ai_template_runner.providers.post_json')
    def test_top_k_limits_the_chunks(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        text = str(self.retrieve(self.make_memory(top_k=1), 'BRAVO please'))

        self.assertEqual(text, PARAGRAPH_TWO)

    @patch('src.ai_template_runner.providers.post_json')
    def test_min_score_filters_weak_chunks(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        text = str(self.retrieve(self.make_memory(min_score=0.5), 'BRAVO please'))

        self.assertEqual(text, PARAGRAPH_TWO)

    @patch('src.ai_template_runner.providers.post_json')
    def test_max_chars_caps_the_injected_context(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        text = str(self.retrieve(
            self.make_memory(max_chars=len(PARAGRAPH_TWO) + len(PARAGRAPH_ONE) + 1),
            'BRAVO please',
        ))

        # the first ranked chunk fits, but the second plus the separator would not
        self.assertEqual(text, PARAGRAPH_TWO)

    @patch('src.ai_template_runner.providers.post_json')
    def test_unknown_collection_is_a_clear_value_error(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        memory_session = session(self.make_memory(), 'BRAVO please', [], self.root / 'template.md')

        with self.assertRaises(ValueError) as err:
            memory_session.ghost

        self.assertIn('ghost', str(err.exception))
        self.assertIn('notes', str(err.exception))

    @patch('src.ai_template_runner.providers.post_json')
    def test_sources_hash_gates_the_rebuild(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        notes = self.write(NOTES_FILE, NOTES_TEXT)

        self.retrieve(self.make_memory(), 'BRAVO please')
        after_build = mock_post_json.call_count  # chunks + query

        self.retrieve(self.make_memory(), 'BRAVO again')
        self.assertEqual(mock_post_json.call_count, after_build + 1)  # query only, db reused

        self.write(NOTES_FILE, NOTES_TEXT + '\n\nCHARLIE segment adds a third thing.')
        self.retrieve(self.make_memory(), 'BRAVO once')
        after_edit = mock_post_json.call_count
        self.assertGreaterEqual(after_edit, after_build + 3)  # full re-embed + query

    @patch('src.ai_template_runner.providers.post_json')
    def test_changed_params_rebuild_without_source_change(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        self.retrieve(self.make_memory(), 'BRAVO please')
        after_build = mock_post_json.call_count

        self.retrieve(self.make_memory(chunk_size=1023), 'BRAVO again')

        self.assertGreater(mock_post_json.call_count, after_build + 1)

    @patch('src.ai_template_runner.providers.post_json')
    def test_empty_retrieval_renders_empty_context(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        self.write(NOTES_FILE, NOTES_TEXT)

        text = str(self.retrieve(self.make_memory(min_score=2.0), 'BRAVO please'))

        self.assertEqual(text, '')


class TestProcessPromptMemory(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def memory_template(self, prompt: str, system: str = '') -> Path:
        self.write(NOTES_FILE, NOTES_TEXT)
        lines = [
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '[memory]',
            'base_url = "http://localhost:8081/v1/embeddings"',
            'model = "emb-test"',
            'source = "notes/task-notes.md"',
            'db = "memory/memory.db"',
            'chunk_size = 64',
            'chunk_overlap = 8',
            '[memory.notes]',
            '```',
        ]
        body = ['---', system, '---'] if system else []
        body.append(prompt)

        return self.write('memory.md', '\n'.join(lines + body))

    @patch('src.ai_template_runner.providers.post_json')
    def test_prompt_contains_the_retrieved_notes(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        template = process_template(self.memory_template('Notes: {memory.notes}\nQuestion: {question}'))

        prompt = process_prompt(template, 'BRAVO please', [], self.root / 'memory.md')

        self.assertIn('BRAVO', prompt)
        self.assertLess(prompt.index('BRAVO'), prompt.index('ARTICLE'))
        self.assertIn('Question: BRAVO please', prompt)

    @patch('src.ai_template_runner.providers.post_json')
    def test_system_prompt_and_user_prompt_share_the_session(self, mock_post_json):
        mock_post_json.side_effect = fake_post_json
        template = process_template(self.memory_template(
            'Notes: {memory.notes}', system='Rules with notes: {memory.notes}',
        ))

        process_system_prompt(template, 'BRAVO please', [], self.root / 'memory.md')
        process_prompt(template, 'BRAVO please', [], self.root / 'memory.md')

        self.assertEqual(mock_post_json.call_count, 2)  # chunks + query, shared session

    def test_unknown_memory_placeholder_when_memory_is_absent(self):
        template = process_template(self.write('plain.md', '\n'.join([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080/v1/chat/completions"',
            'model = "test-model"',
            '```',
            'prompt {memory.notes}',
        ])))

        with self.assertRaises(ValueError) as err:
            process_prompt(template, 'q', [], self.root / 'plain.md')

        self.assertIn('{memory.*}', str(err.exception))
