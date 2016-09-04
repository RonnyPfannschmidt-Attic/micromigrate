from pathlib import Path
from .util import parse_migration


def find_in_path(name_or_path):
    path = Path(name_or_path)
    for item in path.rglob('*.sql'):
        yield parse_migration(item.read_text('utf-8'))
