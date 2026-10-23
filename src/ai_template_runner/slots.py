"""Interpolation of the run slots ({question}, {0}, {1}...) into raw text.

One machinery for every non-prompt text that carries slots: the [memory]
collection query and the values of the [cmd] table. Prompts keep their
own interpolate() because they also resolve {cmd.*} and {memory.*}.
"""

import re
from pathlib import Path

from .output import Smart


def interpolate_slots(
    text: str,
    question,
    args,
    template_path,
    where: str = '',
    cmd=None,
) -> str:
    """Format text with the run slots; Smart values, same as prompts.

    `where` labels the config site in the error messages (e.g.
    'in [cmd] message' or 'in [memory.notes] query') so the usage error
    points where the bad placeholder lives. `cmd`, when given, is a
    CommandView — so config texts like the [memory] query can run
    {cmd.*} placeholders with the same run context.
    """
    path_value = (
        str(Path(template_path).resolve())
        if template_path is not None
        else ''
    )
    slots = ([question] if question is not None else []) + list(args or [])

    try:
        return text.format(
            Smart(path_value),
            *[Smart(value) for value in slots],
            question=(
                Smart(question)
                if isinstance(question, str)
                else question
            ),
            **({'cmd': cmd} if cmd is not None else {}),
        ).strip()
    except KeyError as error:
        raise ValueError(
            f'usage error: unknown placeholder "{error.args[0]}" {where} '
            '(available: {question}, {0}, {1}, {2}...)'
        ) from None
    except IndexError as error:
        match = re.search(r'Replacement index (\d+)', str(error))
        index = match.group(1) if match else '?'
        raise ValueError(
            f'usage error: not enough args {where}: '
            f'slot {{{index}}} requested, got {len(slots)} arg(s)'
        ) from None
    except ValueError as error:
        if 'cannot switch from' in str(error):
            raise ValueError(
                'usage error: {} cannot be mixed with {0}-style numbered '
                'slots (use {0}, {1}, {2}...)'
            ) from None
        raise
