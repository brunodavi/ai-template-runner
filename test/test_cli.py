from unittest import TestCase
from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path

from src.ai_template_runner.cli import cli

from test.helpers import get_root

ROOT = get_root()

def make_post_json(content: str = 'TESTING'):
    return {
        'choices': [
            {
                'message': {
                    'content': content
                }
            }
        ]
    }

def get_template(name: str) -> str:
    return str(ROOT / 'examples' / 'features' / f'{name}.md')


def memory_vectors(text: str) -> list[float]:
    """Deterministic embeddings: 'offline' leans to the RECALL note."""
    if 'RECALL' in text or 'offline' in text:
        return [1.0, 0.0]

    if 'NOTE' in text:
        return [0.0, 1.0]

    raise ValueError(f'unexpected embedding request: {text!r}')


def memory_post_json(url, payload):
    """Two-stage dispatcher: 'input' payloads are embeddings, the rest is chat."""
    if 'input' in payload:
        return {
            'data': [
                {'embedding': memory_vectors(text)} for text in payload['input']
            ]
        }

    return make_post_json()

class TestCli(TestCase):
    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_hello(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('hello')

        with redirect_stdout(output):
            cli(['run', template])

        output_str = output.getvalue()

        self.assertIn('Hello', output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_hello_and_flag_quiet(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('hello')

        with redirect_stdout(output):
            cli(['run', template, '-q'])

        output_str = output.getvalue()

        self.assertEqual(output_str, 'TESTING\n')

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_simple(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('simple')
        question = 'My Question'

        with redirect_stdout(output):
            cli(['run', template, question])

        output_str = output.getvalue()

        self.assertIn(question, output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_command(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('command')
        question = 'My Question'

        with redirect_stdout(output):
            cli(['run', template, question])

        output_str = output.getvalue()

        self.assertNotIn('echo', output_str)
        self.assertIn('hello', output_str)
        self.assertIn(f'{question} interpolated', output_str)
        self.assertIn(question, output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_extras(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()
        template = get_template('extras')

        with redirect_stdout(output):
            cli(['run', template])

        payload = mock_post_json.call_args.args[1]
        output_str = output.getvalue()

        self.assertEqual(payload['typical_p'], 0.95)
        self.assertEqual(payload['repeat_last_n'], 64)
        self.assertEqual(payload['mirostat'], 0)

        self.assertNotIn('{question}', output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_system(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('system')
        question = 'My Question'

        with redirect_stdout(output):
            cli(['run', template, question])

        payload = mock_post_json.call_args.args[1]
        output_str = output.getvalue()

        messages = payload['messages']

        self.assertEqual(messages[0]['role'], 'system')
        self.assertIn('concise assistant', messages[0]['content'])

        self.assertEqual(messages[1]['role'], 'user')
        self.assertIn('hello', messages[1]['content'])
        self.assertNotIn('echo', messages[1]['content'])
        self.assertIn(question, messages[1]['content'])

        self.assertIn('You are a concise assistant', output_str)
        self.assertIn(question, output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_full(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()
        template = get_template('full')

        with redirect_stdout(output):
            cli(['run', template])

        payload = mock_post_json.call_args.args[1]

        expected_fields = {
            'model',
            'messages',
            'temperature',
            'top_p',
            'top_k',
            'min_p',
            'max_tokens',
            'stop',
            'seed',
            'frequency_penalty',
            'presence_penalty',
            'repeat_penalty',
            'stream',
            'typical_p',
            'repeat_last_n',
            'mirostat',
            'mirostat_tau',
            'mirostat_eta',
        }

        self.assertEqual(set(payload.keys()), expected_fields)



    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_output(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json(
            '{"type": "feat", "message": "add endpoint"}',
        )

        output = StringIO()

        template = get_template('output')

        with redirect_stdout(output):
            cli(['run', template])

        output_str = output.getvalue()

        self.assertIn('feat: add endpoint', output_str)
        self.assertNotIn('"message"', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_transforms(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json(
            '{"type": "feat", "message": "  add GET_health endpoint  "}',
        )

        output = StringIO()

        template = get_template('transforms')
        question = '  My Question  '

        with redirect_stdout(output):
            cli(['run', template, question])

        output_str = output.getvalue()

        # [out] steps run in document order over the rendered text
        self.assertIn('FEAT: ADD GET ENDPOINT', output_str)
        self.assertNotIn('"type": "feat"', output_str)

        # the prompt interpolates the question through :strip
        payload = mock_post_json.call_args.args[1]
        prompt_content = ' '.join(
            message['content'] for message in payload['messages']
        )

        self.assertIn('My Question', prompt_content)
        self.assertNotIn('  My Question  ', prompt_content)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_args(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        template = get_template('args')

        with redirect_stdout(StringIO()):
            cli(['run', template, 'one', 'two'])

        content = mock_post_json.call_args.args[1]['messages'][1]['content']

        self.assertIn(str(Path(template).resolve()), content)
        self.assertIn(f'{str(Path(template).resolve())[1:]}', content)
        self.assertIn('one', content)
        self.assertIn('two', content)



class TestCliRunWithTests(TestCase):
    def write_template(self, *lines: str) -> str:
        from tempfile import TemporaryDirectory

        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        path = Path(tmp.name) / 'template.md'
        path.write_text('\n'.join(lines))
        return str(path)

    @patch('src.ai_template_runner.providers.post_json')
    def test_passing_checks_reported_on_stderr(self, mock_post_json: MagicMock):
        mock_post_json.return_value = make_post_json('{"type": "feat"}')

        template = self.write_template(
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[test]',
            'type = "feat"',
            '```',
            'prompt',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            cli(['run', template, '--test'])

        self.assertIn('PASS type', stderr.getvalue())
        self.assertIn('{"type": "feat"}', stdout.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_failing_checks_exit_with_code_1(self, mock_post_json: MagicMock):
        mock_post_json.return_value = make_post_json('TESTING')

        template = self.write_template(
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[test]',
            'type = "feat"',
            '```',
            'prompt',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', template, '--test'])

        self.assertEqual(err.exception.code, 1)
        self.assertIn('FAIL type', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_out_renders_display_but_test_checks_raw(self, mock_post_json: MagicMock):
        mock_post_json.return_value = make_post_json(
            '{"type": "feat", "message": "add endpoint"}',
        )

        template = self.write_template(
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[out]',
            "text = '{out.type}: {out.message}'",
            '[[out.upper]]',
            '[test]',
            'type = "feat"',
            '```',
            'prompt',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            cli(['run', template, '--test'])

        stdout_str = stdout.getvalue()

        self.assertIn('FEAT: ADD ENDPOINT', stdout_str)
        self.assertNotIn('"message"', stdout_str)
        self.assertIn('PASS type', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_template_without_test_table_passes_silently(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json('TESTING')

        template = self.write_template(
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '```',
            'prompt',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            cli(['run', template, '--test'])

        self.assertEqual(stderr.getvalue(), '')


PROVIDER_BLOCK = [
    '```toml',
    '[provider]',
    'base_url = "http://localhost:8080"',
    'model = "test-model"',
    '```',
]


class TestCliRunArgs(TestCase):
    """`ait run TEMPLATE [args...]`: args fill {1}, {2}... and
    {question} stays the alias of {1}."""

    def write_template(self, *lines: str) -> str:
        from tempfile import TemporaryDirectory

        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        path = Path(tmp.name) / 'template.md'
        path.write_text('\n'.join(lines))
        return str(path)

    @patch('src.ai_template_runner.providers.post_json')
    def test_numbered_placeholders_map_to_template_and_args(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        template = self.write_template(
            *PROVIDER_BLOCK,
            '---',
            'args: {1} {2}',
            'question: {question}',
            'path: {0[1:]}',
        )

        with redirect_stdout(StringIO()):
            cli(['run', template, 'one', 'two'])

        content = mock_post_json.call_args.args[1]['messages'][1]['content']

        self.assertIn('args: one two', content)
        self.assertIn('question: one', content)
        self.assertIn(f'path: {str(Path(template).resolve())[1:]}', content)

    @patch('src.ai_template_runner.providers.post_json')
    def test_missing_args_fail_with_friendly_error(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        template = self.write_template(
            *PROVIDER_BLOCK,
            '---',
            'third: {3}',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', template, 'one'])

        self.assertEqual(err.exception.code, 1)
        self.assertIn('not enough args', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_unknown_placeholder_fails_with_friendly_error(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        template = self.write_template(
            *PROVIDER_BLOCK,
            '---',
            'prompt {missing_name}',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', template])

        self.assertEqual(err.exception.code, 1)
        self.assertIn('unknown placeholder', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_args_after_dashdash_are_verbatim(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        template = self.write_template(
            *PROVIDER_BLOCK,
            '---',
            'args: {1} {2} {3}',
        )

        stdout = StringIO()

        with redirect_stdout(stdout):
            cli(['run', template, 'one', '--', '-t', '--test'])

        content = mock_post_json.call_args.args[1]['messages'][1]['content']

        self.assertIn('args: one -t --test', content)

    @patch('src.ai_template_runner.providers.post_json')
    def test_flag_between_and_before_args_is_parsed(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json('{"type": "feat"}')

        template = self.write_template(
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[test]',
            'type = "feat"',
            '```',
            '---',
            'args: {1} {2}',
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            cli(['run', '-t', template, 'one', '--test', 'two'])

        content = mock_post_json.call_args.args[1]['messages'][1]['content']

        self.assertIn('args: one two', content)
        self.assertIn('PASS type', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_no_args_keeps_question_empty(self, mock_post_json: MagicMock):
        mock_post_json.return_value = make_post_json()

        template = self.write_template(
            *PROVIDER_BLOCK,
            '---',
            'question: [{question}]',
        )

        stdout = StringIO()

        with redirect_stdout(stdout):
            cli(['run', template])

        content = mock_post_json.call_args.args[1]['messages'][1]['content']

        self.assertIn('question: []', content)


class TestCliRunTemplates(TestCase):
    """Template resolution, batch runs and content filtering."""

    def setup_dir(self, files: dict[str, str]) -> Path:
        from tempfile import TemporaryDirectory

        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)

        for name, content in files.items():
            (Path(tmp.name) / name).write_text(content)

        return Path(tmp.name)

    @patch('src.ai_template_runner.providers.post_json')
    def test_batch_runs_every_template_in_order(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        directory = self.setup_dir(
            {
                'a.md': '\n'.join(PROVIDER_BLOCK + ['---', 'prompt a']),
                'b.md': '\n'.join(PROVIDER_BLOCK + ['---', 'prompt b']),
            }
        )

        stdout = StringIO()

        with redirect_stdout(stdout):
            cli(['run', f'{directory}/*.md'])

        stdout_str = stdout.getvalue()

        self.assertIn('prompt a', stdout_str)
        self.assertIn('prompt b', stdout_str)
        self.assertIn('Running template: a.md', stdout_str)
        self.assertIn('Running template: b.md', stdout_str)
        self.assertIn('summary: 2/2 templates ok', stdout_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_batch_skips_non_template_files_with_warning(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        directory = self.setup_dir(
            {
                'readme.md': '# just documentation, no toml block',
                'a.md': '\n'.join(PROVIDER_BLOCK + ['---', 'prompt a']),
            }
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            cli(['run', f'{directory}/*.md'])

        self.assertIn('warning: skipped readme.md (not a template)', stderr.getvalue())
        self.assertIn('prompt a', stdout.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_single_non_template_candidate_hard_fails(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        directory = self.setup_dir({'readme.md': '# documentation'})

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', f'{directory}/readme.md'])

        self.assertEqual(err.exception.code, 1)
        mock_post_json.assert_not_called()
        self.assertIn('not a template', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_unmatched_template_is_a_usage_error(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        directory = self.setup_dir({'a.md': '\n'.join(PROVIDER_BLOCK)})

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', f'{directory}/missing/*.md'])

        self.assertEqual(err.exception.code, 1)
        self.assertIn('no template matched', stderr.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_batch_exit_1_when_any_check_fails(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.side_effect = [make_post_json('TESTING'), make_post_json('{"type": "feat"}')]

        directory = self.setup_dir(
            {
                'a.md': '\n'.join(PROVIDER_BLOCK[:-1] + ['[test]', 'type = "feat"', '```', '---', 'prompt a']),
                'b.md': '\n'.join(PROVIDER_BLOCK[:-1] + ['[test]', 'type = "feat"', '```', '---', 'prompt b']),
            }
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', f'{directory}/*.md', '--test'])

        self.assertEqual(err.exception.code, 1)
        self.assertIn('FAIL type', stderr.getvalue())
        self.assertIn('summary: 1/2 templates ok, 1 with FAIL', stdout.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_fail_fast_stops_at_first_failing_template(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.side_effect = [make_post_json('TESTING'), make_post_json('{"type": "feat"}')]

        directory = self.setup_dir(
            {
                'a.md': '\n'.join(PROVIDER_BLOCK[:-1] + ['[test]', 'type = "feat"', '```', '---', 'prompt a']),
                'b.md': '\n'.join(PROVIDER_BLOCK[:-1] + ['[test]', 'type = "feat"', '```', '---', 'prompt b']),
            }
        )

        stdout, stderr = StringIO(), StringIO()

        with redirect_stdout(stdout), redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as err:
                cli(['run', f'{directory}/*.md', '--test', '--fail-fast'])

        self.assertEqual(err.exception.code, 1)
        self.assertEqual(mock_post_json.call_count, 1)
        self.assertIn('fail-fast', stderr.getvalue())
        self.assertNotIn('prompt b', stdout.getvalue())

    @patch('src.ai_template_runner.providers.post_json')
    def test_quiet_batch_prints_one_response_per_line(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        directory = self.setup_dir(
            {
                'a.md': '\n'.join(PROVIDER_BLOCK + ['---', 'prompt a']),
                'b.md': '\n'.join(PROVIDER_BLOCK + ['---', 'prompt b']),
            }
        )

        stdout = StringIO()

        with redirect_stdout(stdout):
            cli(['run', f'{directory}/*.md', '-q'])

        self.assertEqual(stdout.getvalue(), 'TESTING\nTESTING\n')


class TestCliMemory(TestCase):
    def setUp(self):
        # the example db is a generated artifact: fresh build per test
        (ROOT / 'examples' / 'features' / 'memory.db').unlink(missing_ok=True)

    @patch('src.ai_template_runner.providers.post_json')
    def test_memory_notes_reach_the_prompt_in_relevance_order(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.side_effect = memory_post_json

        output = StringIO()

        with redirect_stdout(output):
            cli(['run', get_template('memory'), 'offline runner'])

        # chunk batch + query embedding + chat
        self.assertEqual(mock_post_json.call_count, 3)

        chunk_input = mock_post_json.call_args_list[0].args[1]['input']
        query_input = mock_post_json.call_args_list[1].args[1]['input']
        self.assertEqual(len(chunk_input), 2)  # both notes in one batch
        self.assertEqual(query_input, ['offline runner'])

        prompt = mock_post_json.call_args_list[2].args[1]['messages'][1]['content']
        self.assertIn('offline runner', prompt)
        self.assertIn('RECALL fact', prompt)
        self.assertLess(prompt.index('RECALL fact'), prompt.index('NOTE fact'))

    @patch('src.ai_template_runner.providers.post_json')
    def test_memory_index_is_reused_while_the_hash_matches(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.side_effect = memory_post_json

        with redirect_stdout(StringIO()):
            cli(['run', get_template('memory'), 'offline runner'])

        after_build = mock_post_json.call_count  # chunk batch + query + chat
        self.assertEqual(after_build, 3)

        with redirect_stdout(StringIO()):
            cli(['run', get_template('memory'), 'offline runner'])

        # the fingerprint still matches, so only the query and the chat run
        self.assertEqual(mock_post_json.call_count, after_build + 2)
