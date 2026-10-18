from unittest import TestCase

from src.ai_template_runner.processor import (
    process_prompt,
    process_system_prompt,
)
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


class TestProcessSystemPrompt(TestCase):
    def test_system_prompt_with_only_template(self):
        template = Template('prompt', system_prompt='system')

        system_prompt = process_system_prompt(template)

        self.assertEqual(system_prompt, 'system')

    def test_system_prompt_with_question(self):
        template = Template(
            'prompt {question}',
            system_prompt='Answer {question} concisely.',
        )
        question = 'test'

        system_prompt = process_system_prompt(template, question)

        self.assertEqual(system_prompt, 'Answer test concisely.')

    def test_system_prompt_with_cmd(self):
        template = Template(
            'prompt',
            system_prompt='Context: {cmd.message}',
            cmd=Command(message='echo hello'),
        )

        system_prompt = process_system_prompt(template)

        self.assertEqual(system_prompt, 'Context: hello')

    def test_system_prompt_empty(self):
        template = Template('prompt')

        system_prompt = process_system_prompt(template, 'test')

        self.assertEqual(system_prompt, '')
