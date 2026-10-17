from pathlib import Path
from tomllib import loads

from .models.template import Template
from .models.provider import Provider

def process_template(template_path: Path) -> Template:
    template_str = template_path.read_text()
    [toml_str, prompt] = template_str.split('+++', maxsplit=1)

    toml = loads(toml_str)
    template = Template(
        Provider(**toml),
        prompt
    )

    return template

def process_prompt(template: Template, question: str) -> str:
    prompt = template.user_prompt.format(question=question)

    return prompt
