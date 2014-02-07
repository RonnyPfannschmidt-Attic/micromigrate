import py
from .util import parse_migration


def find_in_path(name_or_path):
    path = py.path.local(name_or_path)
    for item in path.visit('*.sql'):
        yield parse_migration(item.read())
