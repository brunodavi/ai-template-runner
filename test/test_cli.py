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


