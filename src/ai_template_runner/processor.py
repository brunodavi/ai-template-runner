from pathlib import Path
from tomllib import loads

from .models.template import Template
from .models.provider import Provider
from .command import Command

TOML_FENCE = '```toml'
FENCE_END = '```'
SYSTEM_SEPARATOR = '---'


def extract_toml_block(template_str: str) -> tuple[str, str]:
    """Extract the TOML configuration block from the template.

    The block must be the first content of the Markdown file and is
    delimited by a ```toml fenced code block. Returns the TOML source
    and the template content without the block.
    """
    lines = template_str.splitlines()

    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1

    if start == len(lines) or lines[start].strip() != TOML_FENCE:
        raise ValueError(
            "Template must begin with a '```toml' configuration block"
        )

    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if lines[i].strip() == FENCE_END
        ),
        None,
    )

    if end is None:
        raise ValueError(
            "The '```toml' configuration block is not closed"
        )

    toml_str = '\n'.join(lines[start + 1:end])
    content = '\n'.join(lines[end + 1:])

    return toml_str, content


def split_prompts(content: str) -> tuple[str, str]:
    """Split the template content into a system prompt and a user prompt.

    The system prompt is optional and delimited by two '---' separators.
    Everything after the second separator is the user prompt.
    """
    lines = content.splitlines()
    separators = [
        i for i, line in enumerate(lines) if line.strip() == SYSTEM_SEPARATOR
    ]

    if len(separators) < 2:
        return '', content.strip()

    [first, second] = separators[:2]
    system_prompt = '\n'.join(lines[first + 1:second])
    user_prompt = '\n'.join(lines[second + 1:])

    return system_prompt.strip(), user_prompt.strip()


def process_template(template_path: Path) -> Template:
    template_str = template_path.read_text()

    toml_str, content = extract_toml_block(template_str)

    config = loads(toml_str)

    provider = config.get('provider', {})
    cmd = config.get('cmd', {})

    if not provider.get('base_url') or not provider.get('model'):
        raise ValueError(
             "Provider 'base_url' and 'model' are required"
        )

    system_prompt, user_prompt = split_prompts(content)

    template = Template(
        user_prompt,
        system_prompt=system_prompt,
        provider=Provider(**provider),
        cmd=Command(**cmd),
    )

    return template


def interpolate(text: str, template: Template, question: str | None) -> str:
    return text.format(
        question=question,
        cmd=template.cmd,
    ).strip()


def process_prompt(
        template: Template,
        question: str | None = None
    ) -> str:

    return interpolate(template.user_prompt, template, question)


def process_system_prompt(
        template: Template,
        question: str | None = None
    ) -> str:

    return interpolate(template.system_prompt, template, question)
