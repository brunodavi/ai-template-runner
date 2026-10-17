from unittest import TestCase

from src.ai_template_runner.runtime import process_template


class TestProcessTemplate(TestCase):
    def test_template_with_provider_and_prompt_simple(self):
        class FakePath:
            def read_text(self):
                return '\n'.join([
                    'base_url = "http://localhost:8080"',
                    'model = "test-model"',
                    '+++',
                    'prompt',
                ])

        template = process_template(FakePath())

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.temperature, None)
        self.assertEqual(template.provider.top_k, None)
        self.assertEqual(template.provider.top_p, None)
        self.assertEqual(template.provider.max_tokens, None)
        self.assertEqual(template.provider.seed, None)
        self.assertEqual(template.provider.stop, [])

        self.assertEqual(template.user_prompt, '\nprompt')

    def test_template_with_provider_and_prompt_full(self):
        class FakePath:
            def read_text(self):
                return '\n'.join([
                    'base_url = "http://localhost:8080"',
                    'model = "test-model"',
                    'temperature = 1.0',
                    'top_p = 1.0',
                    'top_k = 1.0',
                    'max_tokens = 220',
                    'seed = 42',
                    'stop = ["."]',
                    '+++',
                    'prompt',
                ])

        template = process_template(FakePath())

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.temperature, 1.0)
        self.assertEqual(template.provider.top_k, 1.0)
        self.assertEqual(template.provider.top_p, 1.0)
        self.assertEqual(template.provider.max_tokens, 220)
        self.assertEqual(template.provider.seed, 42)
        self.assertEqual(template.provider.stop, ['.'])

        self.assertEqual(template.user_prompt, '\nprompt')

    def test_template_with_douple_splits_and_config(self):
        class FakePath:
            def read_text(self):
                return '\n'.join([
                    'base_url = "http://localhost:8080"',
                    'model = "test-model"',
                    'temperature = 1.0',
                    'top_p = 1.0',
                    'top_k = 1.0',
                    'max_tokens = 220',
                    'seed = 42',
                    'stop = ["."]',
                    '+++',
                    '+++',
                    'prompt',
                ])

        template = process_template(FakePath())

        self.assertEqual(template.provider.base_url, 'http://localhost:8080')
        self.assertEqual(template.provider.model, 'test-model')
        self.assertEqual(template.provider.temperature, 1.0)
        self.assertEqual(template.provider.top_k, 1.0)
        self.assertEqual(template.provider.top_p, 1.0)
        self.assertEqual(template.provider.max_tokens, 220)
        self.assertEqual(template.provider.seed, 42)
        self.assertEqual(template.provider.stop, ['.'])

        self.assertEqual(template.user_prompt, '\n+++\nprompt')

    def test_template_no_provider(self):
        class FakePath:
            def read_text(self):
                return '\n'.join([
                    '+++',
                    'prompt',
                ])

        with self.assertRaises(Exception):
            process_template(FakePath())

    def test_template_with_error(self):
        class FakePath:
            def read_text(self):
                raise Exception()

        with self.assertRaises(Exception):
            process_template(FakePath())
