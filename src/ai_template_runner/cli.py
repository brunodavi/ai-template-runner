from argparse import ArgumentParser
from pathlib import Path
import sys

from .processor import (
    process_template,
    process_prompt,
    process_system_prompt,
)
from .providers import llamacpp
from .checks import run_checks
from .output import render_out


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

    run.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Show only the AI response",
    )

    run.add_argument(
        "-t", "--test",
        action="store_true",
        help="Validate the AI response against the [test] table",
    )

    args = parser.parse_args(argv)

    if args.command == "run":
        template_path: Path = args.template_path

        if not args.quiet:
            print(f"Running template: {template_path.name}\n")

        template = process_template(template_path)
        prompt = process_prompt(template, args.question)
        system_prompt = process_system_prompt(template, args.question)

        if not args.quiet and system_prompt:
            print("System:", system_prompt)
            print()

        if not args.quiet:
            print("User:", prompt)
            print()

        response_json = llamacpp(
            template.provider,
            prompt,
            system_prompt,
        )

        ai_response = (
            response_json["choices"][0]["message"]["content"]
        )

        rendered = render_out(template.out, ai_response)

        if args.quiet:
            print(rendered)
        else:
            print("AI:", rendered)

        if args.test:
            failed = False

            for result in run_checks(template.test, ai_response):
                status = 'PASS' if result.passed else 'FAIL'
                line = f'{status} {result.name}' + (f': {result.detail}' if result.detail else '')
                print(line, file=sys.stderr)
                failed = failed or not result.passed

            if failed:
                raise SystemExit(1)
