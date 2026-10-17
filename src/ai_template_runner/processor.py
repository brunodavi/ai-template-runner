from pathlib import Path
from tomllib import loads

from .models.template import Template
from .models.provider import Provider
from .command import Command

def process_template(template_path: Path) -> Template:
    template_str = template_path.read_text()
    [toml_str, prompt] = template_str.split('+++', maxsplit=1)

    toml = loads(toml_str)

    provider = toml.get('provider', {})
    cmd = toml.get('cmd', {})

    if not provider.get('base_url') or not provider.get('model'):
        raise ValueError(
             "Provider 'base_url' and 'model' are required"
        )

    template = Template(
        prompt,
        provider=Provider(**provider),
        cmd=Command(**cmd),
    )

    return template

def process_prompt(template: Template, question: str) -> str:
    prompt = template.user_prompt.format(question=question)

    return prompt.strip()
