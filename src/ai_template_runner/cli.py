import glob
from argparse import ArgumentParser
from pathlib import Path
import sys

from .processor import (
    TOML_FENCE,
    process_template,
    process_prompt,
    process_system_prompt,
)
from .providers import llamacpp
from .checks import run_checks
from .output import render_out


def _usage_error(message: str):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def _resolve_templates(token: str) -> list[Path]:
    """Resolve the template token: literal path first, then glob.

    The token always goes through resolution; single files (absolute
    or relative) resolve directly and pattern matching supports '*',
    '?' and '[]' (with '**' recursion). Matches come out sorted so
    batch runs are deterministic.
    """
    path = Path(token)

    if path.is_file():
        return [path]

    if any(c in token for c in '*?['):
        return sorted(Path(match) for match in glob.glob(token, recursive=True))

    return []


def _is_template(path: Path) -> bool:
    """Templates always start with the ```toml configuration block."""
    try:
        first_line = next(
            line.strip() for line in path.read_text().splitlines() if line.strip()
        )
    except OSError:
        return False

    return first_line == TOML_FENCE


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
        help="Run a template (or a batch of them through a glob pattern)",
        description="Run a template (or a batch of them through a glob pattern)",
    )

    run.add_argument(
        "template",
        help="Template path, or a glob pattern to run multiple templates "
        "(quote patterns so the shell does not expand them)",
    )

    run.add_argument(
        "rest",
        nargs="*",
        help="Values for the {1}, {2}... placeholders ({question} is the "
        "alias of {1}; use -- to pass values that start with '-')",
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

    run.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop the batch at the first template with a FAIL",
    )

    argv = list(argv) if argv is not None else sys.argv[1:]

    if not argv or argv[0] != "run":
        # '--help', no args, or an unknown/grown subcommand: keep the
        # standard argparse behaviour for the top level.
        args = parser.parse_args(argv)

        if args.command == "run":  # pragma: no cover - manual dispatch below
            raise SystemExit("internal dispatch error")

        return

    # Escape hatch: everything after '--' is verbatim arg data (args
    # may start with '-'); the argparse never sees that region.
    argv_left = argv[1:]
    verbatim = []

    if "--" in argv_left:
        cut = argv_left.index("--")
        argv_left, verbatim = argv_left[:cut], argv_left[cut + 1:]

    # parse_intermixed_args lets flags live before, between and after
    # the positional args (a plain parse_args cannot resume a greedy
    # positional after a flag).
    args = run.parse_intermixed_args(argv_left)
    args.rest.extend(verbatim)

    template_token = args.template
    rest = args.rest
    question = rest[0] if rest else ""
    tail_args = rest[1:]

    templates = _resolve_templates(template_token)

    if not templates:
        _usage_error(f"usage error: no template matched: {template_token!r}")

    broken = [path for path in templates if not _is_template(path)]

    if broken:
        if len(templates) == 1:
            _usage_error(
                "usage error: resolved file is not a template "
                f"(missing ```toml block): {templates[0]}"
            )

        if not args.quiet:
            for path in broken:
                print(
                    f"warning: skipped {path.name} (not a template)",
                    file=sys.stderr,
                )

        templates = [path for path in templates if path not in broken]

        if not templates:
            _usage_error("usage error: none of the resolved files is a template")

    failed = 0

    for index, template_path in enumerate(templates):
        if not args.quiet:
            if index:
                print()

            print(f"Running template: {template_path.name}\n")

        try:
            template = process_template(template_path)
            prompt = process_prompt(template, question, tail_args, template_path)
            system_prompt = process_system_prompt(
                template, question, tail_args, template_path
            )

            if not args.quiet:
                if system_prompt:
                    print("System:", system_prompt)
                    print()

                print("User:", prompt)
                print()

            response_json = llamacpp(template.provider, prompt, system_prompt)
            ai_response = response_json["choices"][0]["message"]["content"]
            rendered = render_out(template.out, ai_response)

            print(rendered) if args.quiet else print("AI:", rendered)

            if args.test:
                for result in run_checks(template.test, ai_response):
                    status = "PASS" if result.passed else "FAIL"
                    line = f"{status} {result.name}"
                    line += f": {result.detail}" if result.detail else ""
                    print(line, file=sys.stderr)

                    if not result.passed:
                        failed += 1
        except (ValueError, OSError, KeyError) as error:
            print(f"error: {template_path.name}: {error}", file=sys.stderr)
            failed += 1

        if args.fail_fast and failed:
            print("fail-fast: stopping batch", file=sys.stderr)
            break

    if not args.quiet and len(templates) > 1:
        print(f"summary: {len(templates) - failed}/{len(templates)}"
              f" templates ok, {failed} with FAIL")

    if failed:
        raise SystemExit(1)
