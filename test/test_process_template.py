from unittest import TestCase

from tomllib import TOMLDecodeError

from src.ai_template_runner.processor import (
    extract_toml_block,
    split_prompts,
    process_template,
)


def template_str(*lines: str) -> str:
    return '\n'.join(lines)


class FakePath:
    def __init__(self, lines: list[str]):
        content = template_str(*lines)
        self._content = content

    def read_text(self) -> str:
        return self._content


class TestExtractTomlBlock(TestCase):
    def test_extracts_toml_and_remaining_content(self):
        result = extract_toml_block(template_str(
            '```toml',
            'model = "test"',
            '```',
            '',
            'prompt',
        ))

        self.assertEqual(result[0], 'model = "test"')
        self.assertEqual(result[1], '\nprompt')

    def test_extracts_multiline_toml(self):
        result = extract_toml_block(template_str(
            '```toml',
            '[provider]',
            'model = "test"',
            '[cmd]',
            'message = "echo"',
            '```',
            'prompt',
        ))

        self.assertIn('[provider]', result[0])
        self.assertIn('[cmd]', result[0])
        self.assertEqual(result[1], 'prompt')

    def test_block_must_be_at_the_beginning(self):
        with self.assertRaises(ValueError) as err:
            extract_toml_block(template_str(
                'some text',
                '```toml',
                'model = "test"',
                '```',
            ))

        self.assertIn('```toml', str(err.exception))

    def test_template_without_toml_block(self):
        with self.assertRaises(ValueError) as err:
            extract_toml_block(template_str(
                '[provider]',
                '+++',
                'prompt',
            ))

        self.assertIn('```toml', str(err.exception))

    def test_toml_block_not_closed(self):
        with self.assertRaises(ValueError) as err:
            extract_toml_block(template_str(
                '```toml',
                'model = "test"',
                'prompt',
            ))

        self.assertIn('not closed', str(err.exception))

    def test_empty_template(self):
        with self.assertRaises(ValueError):
            extract_toml_block('')


class TestSplitPrompts(TestCase):
    def test_split_with_system_prompt(self):
        system_prompt, user_prompt = split_prompts(template_str(
            '',
            '---',
            'You are a concise assistant.',
            '---',
            '',
            'Question: {question}',
        ))

        self.assertEqual(system_prompt, 'You are a concise assistant.')
        self.assertEqual(user_prompt, 'Question: {question}')

    def test_split_without_separators(self):
        system_prompt, user_prompt = split_prompts(template_str(
            '',
            'Question: {question}',
        ))

        self.assertEqual(system_prompt, '')
        self.assertEqual(user_prompt, 'Question: {question}')

    def test_split_with_only_one_separator(self):
        system_prompt, user_prompt = split_prompts(template_str(
            '---',
            'Question: {question}',
        ))

        self.assertEqual(system_prompt, '')
        self.assertEqual(user_prompt, '---\nQuestion: {question}')


class TestProcessTemplate(TestCase):
    def test_template_with_provider_and_prompt_simple(self):
        template = process_template(FakePath([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '```',
            '',
            'prompt',
        ]))

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.temperature, None)
        self.assertEqual(template.provider.top_k, None)
        self.assertEqual(template.provider.top_p, None)
        self.assertEqual(template.provider.min_p, None)
        self.assertEqual(template.provider.max_tokens, None)
        self.assertEqual(template.provider.seed, None)
        self.assertEqual(template.provider.stop, [])
        self.assertEqual(template.provider.frequency_penalty, None)
        self.assertEqual(template.provider.presence_penalty, None)
        self.assertEqual(template.provider.repeat_penalty, None)
        self.assertEqual(template.provider.extras, {})

        self.assertEqual(template.user_prompt, 'prompt')
        self.assertEqual(template.system_prompt, '')

    def test_template_with_provider_and_prompt_full(self):
        template = process_template(FakePath([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            'temperature = 1.0',
            'top_p = 0.9',
            'top_k = 40',
            'min_p = 0.05',
            'max_tokens = 220',
            'seed = 42',
            'stop = ["."]',
            'frequency_penalty = 0.2',
            'presence_penalty = 0.1',
            'repeat_penalty = 1.1',
            '```',
            '',
            'prompt',
        ]))

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.temperature, 1.0)
        self.assertEqual(template.provider.top_k, 40)
        self.assertEqual(template.provider.top_p, 0.9)
        self.assertEqual(template.provider.min_p, 0.05)
        self.assertEqual(template.provider.max_tokens, 220)
        self.assertEqual(template.provider.seed, 42)
        self.assertEqual(template.provider.stop, ['.'])
        self.assertEqual(template.provider.frequency_penalty, 0.2)
        self.assertEqual(template.provider.presence_penalty, 0.1)
        self.assertEqual(template.provider.repeat_penalty, 1.1)
        self.assertEqual(template.provider.extras, {})

        self.assertEqual(template.user_prompt, 'prompt')

    def test_template_with_provider_extras(self):
        template = process_template(FakePath([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[provider.extras]',
            'typical_p = 0.95',
            'repeat_last_n = 64',
            'mirostat = 0',
            '```',
            '',
            'prompt',
        ]))

        self.assertEqual(
            template.provider.extras,
            {
                'typical_p': 0.95,
                'repeat_last_n': 64,
                'mirostat': 0,
            },
        )

        self.assertEqual(template.user_prompt, 'prompt')

    def test_template_with_system_prompt(self):
        template = process_template(FakePath([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '```',
            '',
            '---',
            'You are a concise assistant.',
            '---',
            '',
            'Command output: {cmd.message}',
            '',
            'Question: {question}',
        ]))

        self.assertEqual(template.system_prompt, 'You are a concise assistant.')
        self.assertEqual(
            template.user_prompt,
            'Command output: {cmd.message}\n\nQuestion: {question}',
        )

    def test_template_with_cmd(self):
        template = process_template(FakePath([
            '```toml',
            '[provider]',
            'base_url = "http://localhost:8080"',
            'model = "test-model"',
            '[cmd]',
            'message = "echo test"',
            '```',
            '',
            'prompt {cmd.message}',
        ]))

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.extras, {})
        self.assertEqual(template.cmd.message, 'test')

        self.assertEqual(template.user_prompt, 'prompt {cmd.message}')

    def test_template_empty_provider(self):
        with self.assertRaises(ValueError) as err:
            process_template(FakePath([
                '```toml',
                '[provider]',
                '```',
                '',
                'prompt',
            ]))

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))
        self.assertIn('required', str(err.exception))

    def test_template_empty_provider_args_required(self):
        with self.assertRaises(ValueError) as err:
            process_template(FakePath([
                '```toml',
                '[provider]',
                'base_url = ""',
                'model = ""',
                '```',
                '',
                'prompt',
            ]))

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))
        self.assertIn('required', str(err.exception))

    def test_template_no_provider(self):
        with self.assertRaises(ValueError) as err:
            process_template(FakePath([
                '```toml',
                '',
                '```',
                '',
                'prompt',
            ]))

        self.assertIn('base_url', str(err.exception))
        self.assertIn('model', str(err.exception))
        self.assertIn('required', str(err.exception))

    def test_template_with_malformed_toml(self):
        with self.assertRaises(TOMLDecodeError):
            process_template(FakePath([
                '```toml',
                '[provider',
                'base_url = "http://localhost:8080"',
                'model = "test-model"',
                '```',
                '',
                'prompt',
            ]))

    def test_template_without_toml_block_is_malformed(self):
        with self.assertRaises(ValueError) as err:
            process_template(FakePath([
                '[provider]',
                'base_url = "http://localhost:8080"',
                'model = "test-model"',
                '+++',
                'prompt',
            ]))

        self.assertIn('```toml', str(err.exception))

    def test_template_with_error(self):
        class FakePath:
            def read_text(self):
                raise Exception()

        with self.assertRaises(Exception):
            process_template(FakePath())
