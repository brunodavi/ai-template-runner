from unittest import TestCase

from src.ai_template_runner.runtime import process_template


class TestProcessTemplate(TestCase):
    def test_template_with_only_prompt(self):
        class FakePath:
            def read_text(self):
                return 'prompt'

        template = process_template(FakePath())

        self.assertEqual(template.prompt, 'prompt')

        self.assertEqual(template.config.name, None)
        self.assertEqual(template.config.description, None)
        self.assertEqual(template.config.temperature, None)
        self.assertEqual(template.config.top_k, None)
        self.assertEqual(template.config.top_p, None)

    def test_template_with_config_and_prompt(self):
        class FakePath:
            def read_text(self):
                return '\n'.join([
                    'name = "Test"',
                    'description = "Test Description"',
                    'temperature = 1.0',
                    'top_k = 1',
                    'top_p = -1',
                    '+++',
                    'prompt',
                ])

        template = process_template(FakePath())

        self.assertEqual(template.config.name, 'Test')
        self.assertEqual(template.config.description, 'Test Description')
        self.assertEqual(template.config.temperature, 1.0)
        self.assertEqual(template.config.top_k, 1)
        self.assertEqual(template.config.top_p, -1)

        self.assertEqual(template.prompt.strip(), 'prompt')
