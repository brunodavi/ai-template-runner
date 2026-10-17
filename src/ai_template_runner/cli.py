from argparse import ArgumentParser
from pathlib import Path

from .runtime import process_template, process_prompt

def cli(argv: list[str] = None):
    parser = ArgumentParser(
        'ait',
        'Simple AI workflow based on Markdown templates'
    )

    run = parser.add_argument_group(
        'run',
        description='Run a template'
    )

    run.add_argument(
        'template_path',
        help='Path template markdown to run',
        type=Path
    )

    run.add_argument(
        'question',
        help='Question to anwser',
    )

    args = parser.parse_args(argv)

    template_path: Path = args.template_path

    print(f'Running template: {template_path.name}')

    template = process_template(template_path)
    prompt = process_prompt(template, args.question)

    print(f'Asking AI: {prompt}')
