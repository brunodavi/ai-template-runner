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

    def test_prompt_without_question_is_none(self):
        template = Template('prompt {question}')

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'prompt None')


class TestSmartPromptInterpolation(TestCase):
    """Fase 2: {question} and {cmd.field} gain the same inline
    transforms as {out.field} — :method:args spec and [slice]."""

    def test_question_spec_single_method(self):
        template = Template('{question:strip}')

        prompt = process_prompt(template, '  test  ')

        self.assertEqual(prompt, 'test')

    def test_question_spec_with_args(self):
        template = Template('{question:replace:old:new}')
        question = 'the old question'

        prompt = process_prompt(template, question)

        self.assertEqual(prompt, 'the new question')

    def test_question_pythonic_slice(self):
        template = Template('{question[:8]}')
        question = 'question about python'

        prompt = process_prompt(template, question)

        self.assertEqual(prompt, 'question')

    def test_cmd_spec_single_method(self):
        template = Template(
            '{cmd.message:upper}',
            cmd=Command(message='echo hello'),
        )

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'HELLO')

    def test_cmd_pythonic_slice(self):
        template = Template(
            '{cmd.message[:2]}',
            cmd=Command(message='echo hello'),
        )

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'he')

    def test_cmd_spec_with_args(self):
        template = Template(
            "{cmd.message:replace:hello:bye}",
            cmd=Command(message='echo hello'),
        )

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'bye')

    def test_unknown_spec_method_fails_descriptively(self):
        template = Template('{question:banana}')

        with self.assertRaises(ValueError) as ctx:
            process_prompt(template, 'test')

        self.assertIn('banana', str(ctx.exception))

    def test_without_question_spec_remains_plain(self):
        template = Template('[{question}] vs [{question:strip}]')
        question = '  padded question  '

        prompt = process_prompt(template, question)

        # no spec: the raw value keeps its spacing; :strip transforms
        self.assertEqual(prompt, '[  padded question  ] vs [padded question]')


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
