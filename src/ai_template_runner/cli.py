from argparse import ArgumentParser
from pathlib import Path

from .runtime import process_template

def cli(argv: list[str] = None):
    parser = ArgumentParser(
        'ait',
        'Simple AI workflow based on Markdown templates'
    )

    parser.add_argument(
        'template_path',
        help='Path template markdown to run',
        type=Path
    )

    args = parser.parse_args(argv)

    template_path: Path = args.template_path

    print(f'Running template: {template_path.name}')

    template = process_template(template_path)
