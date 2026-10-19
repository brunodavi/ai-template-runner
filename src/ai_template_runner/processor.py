from pathlib import Path
from tomllib import loads

from .models.template import Template
from .models.provider import Provider
from .command import Command

TOML_FENCE = '```toml'
FENCE_END = '```'
SYSTEM_SEPARATOR = '---'

EXTENDS_KEY = 'extends'


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


def merge_configs(parent: dict, child: dict) -> dict:
    """Merge two TOML config dicts, child values win.

    Nested tables (e.g. [provider.extras] or [cmd]) are merged
    per additional table level, so child tables inherit parent keys.
    """
    merged = dict(parent)
    for key, value in child.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_template(
    template_path: Path,
    _extends_stack: frozenset[Path] = frozenset(),
) -> tuple[dict, dict, dict, str, str]:
    """Load a template file and resolve its `extends` chain.

    Returns (provider config, cmd config, test config, system prompt,
    user prompt). The `extends` path is resolved relative to the
    template file itself; parent provider/cmd/test configs are merged
    per key and parent prompts are used wherever the child prompts
    are empty.
    """
    template_str = template_path.read_text()

    toml_str, content = extract_toml_block(template_str)

    config = loads(toml_str)
    extends = config.pop(EXTENDS_KEY, None)

    provider = dict(config.get('provider', {}))
    cmd = dict(config.get('cmd', {}))
    test = dict(config.get('test', {}))

    system_prompt, user_prompt = split_prompts(content)

    if extends:
        parent_path = template_path.parent / extends

        if not parent_path.is_file():
            raise ValueError(
                f"Template 'extends' file not found: {extends}"
            )

        parent_resolved = parent_path.resolve()

        if parent_resolved in _extends_stack:
            raise ValueError(
                f"circular 'extends' in template chain: {extends}"
            )

        parent = load_template(
            parent_path,
            _extends_stack | {parent_resolved},
        )

        parent_provider, parent_cmd, parent_test, parent_system, parent_user = (
            parent
        )

        provider = merge_configs(parent_provider, provider)
        cmd = merge_configs(parent_cmd, cmd)
        test = merge_configs(parent_test, test)

        system_prompt = system_prompt or parent_system
        user_prompt = user_prompt or parent_user

    return provider, cmd, test, system_prompt, user_prompt


def process_template(template_path: Path) -> Template:
    provider_config, cmd_config, test_config, system_prompt, user_prompt = (
        load_template(template_path)
    )

    if not provider_config.get('base_url') or not provider_config.get('model'):
        raise ValueError(
             "Provider 'base_url' and 'model' are required"
        )

    return Template(
        user_prompt,
        system_prompt=system_prompt,
        provider=Provider(**provider_config),
        cmd=Command(**cmd_config),
        test=test_config,
    )


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
