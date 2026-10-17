from argparse import ArgumentParser
from pathlib import Path

from .processor import process_template, process_prompt
from .providers import llamacpp


def cli(argv: list[str] = None):
    parser = ArgumentParser(
        prog="ait",
        description="Simple AI workflow based on Markdown templates",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    run = subparsers.add_parser(
        "run",
        help="Run a template",
        description="Run a template",
    )

    run.add_argument(
        "template_path",
        help="Path template markdown to run",
        type=Path,
    )

    run.add_argument(
        "question",
        help="Question to answer",
        nargs="?",
        default="",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        template_path: Path = args.template_path

        print(f"Running template: {template_path.name}\n")

        template = process_template(template_path)
        prompt = process_prompt(template, args.question)

        print("User:", prompt)
        print()

        result = llamacpp(template.provider, prompt)
        print("AI:", result["choices"][0]["message"]["content"])
