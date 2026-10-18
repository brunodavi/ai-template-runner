from unittest import TestCase

from src.ai_template_runner.processor import process_prompt
from src.ai_template_runner.models.template import Template
from src.ai_template_runner.command import Command


class TestProcessPrompt(TestCase):
    def test_prompt_with_only_template(self):
        template = Template('prompt')

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'prompt')

    def test_prompt_with_question(self):
        template = Template('prompt {question}')
        question = 'test'

        prompt = process_prompt(template, question)

        self.assertEqual(prompt, 'prompt test')

    def test_prompt_with_cmd(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo hello')
        )

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'prompt hello')

    def test_prompt_with_question_and_cmd(self):
        template = Template(
            'prompt {question} {cmd.message}',
            cmd=Command(message='echo hello')
        )
        question = 'test'

        prompt = process_prompt(template, question)

        self.assertEqual(prompt, 'prompt test hello')
