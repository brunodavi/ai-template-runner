from pathlib import Path
from tomllib import loads

from .models.template import Template

def process_template(template_path: Path) -> Template:
    template_str = template_path.read_text()
    template_parts = template_str.split('+++', maxsplit=1)

    prompt = template_parts[-1]
    template = Template(prompt)

    if len(template_parts) == 1:
        return template

    toml_str = template_parts[0]
    toml = loads(toml_str)

    template.config.name = toml.get('name')
    template.config.description = toml.get('description')

    template.config.temperature = toml.get('temperature')
    template.config.top_k = toml.get('top_k')
    template.config.top_p = toml.get('top_p')

    return template
