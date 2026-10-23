"""The [cmd] table: lazy shell commands behind the {cmd.<name>} placeholders.

The value of each command accepts the same run slots as the prompts
({question}, {0}, {1}...) with the Smart transforms; interpolation is
raw (no quoting) and happens right before the subprocess runs, so what
reaches the shell is exactly what the author worded.
"""

import subprocess

from .output import Smart
from .slots import interpolate_slots


class Command:
    """Storage the template gets at load time; each {cmd.<name>}
    reference executes its value."""

    def __init__(self, **kwargs):
        self.commands = kwargs

    def __getattr__(self, name):
        command = self.commands[name]
        return Smart(subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip())


class CommandView:
    """Per-run view over a Command: interpolates the run slots when the
    {cmd.<name>} placeholder is evaluated, then executes the result.

    Built by processor.interpolate on every prompt format call — the
    Template carries no per-run state.
    """

    def __init__(self, command: Command, question, args, template_path):
        self._command = command
        self._question = question
        self._args = list(args or [])
        self._template_path = template_path

    def __getattr__(self, name: str) -> Smart:
        if name.startswith('_'):
            raise AttributeError(name)

        command = self._command.commands[name]  # KeyError → processor usage error

        text = interpolate_slots(
            command,
            self._question,
            self._args,
            self._template_path,
            where=f'in [cmd] {name}',
        )

        return Smart(subprocess.run(
            text,
            shell=True,
            capture_output=True,
            text=True
        ).stdout.strip())
