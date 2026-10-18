from unittest import TestCase
from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout
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
    return str(ROOT / 'examples' / f'{name}.md')

class TestCli(TestCase):
    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_hello(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()

        template = get_template('template-hello')

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

        template = get_template('template-hello')

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

        template = get_template('template-simple')
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

        template = get_template('template-command')
        question = 'My Question'

        with redirect_stdout(output):
            cli(['run', template, question])

        output_str = output.getvalue()

        self.assertNotIn('echo', output_str)
        self.assertIn('hello', output_str)
        self.assertIn(question, output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_extras(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()
        template = get_template('template-extras')

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

        template = get_template('template-system')
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

        self.assertNotIn('You are a concise assistant', output_str)
        self.assertIn(question, output_str)
        self.assertIn('TESTING', output_str)

    @patch('src.ai_template_runner.providers.post_json')
    def test_cli_run_with_template_full(
        self,
        mock_post_json: MagicMock,
    ):
        mock_post_json.return_value = make_post_json()

        output = StringIO()
        template = get_template('template-full')

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
