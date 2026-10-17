from unittest import TestCase

from src.ai_template_runner.runtime import process_prompt
from src.ai_template_runner.models.template import Template


class TestProcessPrompt(TestCase):
    def test_prompt_with_question(self):
        template = Template(
            None,
            user_prompt='prompt {question}'
        )
        question = 'test'

        prompt = process_prompt(template, question)

        self.assertEqual(prompt, 'prompt test')
