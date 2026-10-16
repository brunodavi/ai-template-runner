from argparse import ArgumentParser

def cli(argv: list[str] = None):
    parser = ArgumentParser(
        'ait',
        'Simple AI workflow based on Markdown templates'
    )

    parser.add_argument(
        'template',
        help='Template markdown to run'
    )

    args = parser.parse_args(argv)
    print(f'Running template: {args.template}')
