from unittest import TestCase

from src.ai_template_runner.command import Command

class TestCommand(TestCase):
    def test_command_with_one_command(self):
        cmd = Command(message='echo test')

        self.assertEqual(cmd.message, 'test')

    def test_command_with_many_commands(self):
        cmd = Command(
            a='echo A',
            b='echo B',
            c='echo C',
        )

        self.assertEqual(cmd.a, 'A')
        self.assertEqual(cmd.b, 'B')
        self.assertEqual(cmd.c, 'C')

    def test_command_with_format(self):
        cmd = Command(message='echo test')
        result = '{cmd.message}'.format(cmd=cmd)

        self.assertEqual(result, 'test')

