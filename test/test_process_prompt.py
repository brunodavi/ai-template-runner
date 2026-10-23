from unittest import TestCase
from pathlib import Path

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


class TestCmdSlotInterpolation(TestCase):
    """[cmd] values accept the same run slots as the prompts; the
    {cmd.<name>} reference interpolates the value right before the
    subprocess runs (lazy, like the [memory] collection query)."""

    def test_cmd_value_interpolates_question(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo "{question}"'),
        )

        prompt = process_prompt(template, 'hello world')

        self.assertEqual(prompt, 'prompt hello world')

    def test_cmd_value_interpolates_positional_slots(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo first={1} second={2}'),
        )

        prompt = process_prompt(template, 'alpha', ['beta'])

        self.assertEqual(prompt, 'prompt first=alpha second=beta')

    def test_cmd_value_interpolates_path_slot(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo run={0}'),
        )
        expected = str(Path('/tmp/opencode/run.md').resolve())

        prompt = process_prompt(
            template, 'test', template_path=Path('/tmp/opencode/run.md')
        )

        self.assertEqual(prompt, f'prompt run={expected}')

    def test_cmd_value_supports_spec_transforms(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo {question:strip}'),
        )

        prompt = process_prompt(template, '  padded  ')

        self.assertEqual(prompt, 'prompt padded')

    def test_cmd_value_supports_slices(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo {question[:5]}'),
        )

        prompt = process_prompt(template, 'hello world')

        self.assertEqual(prompt, 'prompt hello')

    def test_cmd_value_unknown_placeholder_fails_descriptively(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo {banana}'),
        )

        with self.assertRaises(ValueError) as err:
            process_prompt(template, 'test')

        self.assertIn('banana', str(err.exception))
        self.assertIn('[cmd] message', str(err.exception))
        self.assertIn('unknown placeholder', str(err.exception))

    def test_cmd_value_not_enough_args_fails_descriptively(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo {2}'),
        )

        with self.assertRaises(ValueError) as err:
            process_prompt(template, 'test')

        self.assertIn('not enough args', str(err.exception))
        self.assertIn('[cmd] message', str(err.exception))

    def test_cmd_value_mixed_slot_styles_fail_descriptively(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo {0} {}'),
        )

        with self.assertRaises(ValueError) as err:
            process_prompt(template, 'test')

        self.assertIn('cannot be mixed', str(err.exception))

    def test_cmd_value_doubled_braces_become_literals(self):
        template = Template(
            'prompt {cmd.shout}',
            cmd=Command(shout="echo '{{print 42}}'"),
        )

        prompt = process_prompt(template)

        self.assertEqual(prompt, 'prompt {print 42}')

    def test_cmd_static_value_keeps_running(self):
        template = Template(
            'prompt {cmd.message}',
            cmd=Command(message='echo hello'),
        )

        prompt = process_prompt(template, 'test')

        self.assertEqual(prompt, 'prompt hello')


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
