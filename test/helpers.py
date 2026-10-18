from pathlib import Path

def get_root() -> Path:
    path = Path(__file__).parent

    while not (path / '.git').is_dir():
        path = path.parent

    return path

