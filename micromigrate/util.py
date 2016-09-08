from __future__ import print_function

import subprocess

from hashlib import sha256
from itertools import takewhile

from .types import Migration, KWException


def parse_lineoutput(data):
    chunks = data.split('\n\n')
    return [
        dict(x.strip().split(' = ')
             for x in chunk.splitlines())
        for chunk in chunks if chunk.strip()
    ]


def output_or_raise(*args):
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    out, err = proc.communicate()
    if proc.returncode:
        raise KWException(
            returncode=proc.returncode,
            out=out, err=err)
    return out


def _is_commentline(line):
    return line.startswith('-- ')


def parse_migration(sql):
    """
    parses the metadata of a migration text

    :param sql: text content (unicode on python2) of the migration
    """
    meta = {
        'checksum': sha256(sql.encode('utf-8')).hexdigest(),
        'sql': sql,
        'after': None,
        'name': None
    }
    lines = sql.strip().splitlines()
    lines = takewhile(_is_commentline, lines)
    for line in lines:
        items = line.split()[1:]
        key = items.pop(0)
        if meta['name'] is None:
            assert key == 'migration', \
                'first comment must be migration name'
            assert items
            meta['name'] = items[0]
        else:
            assert key != 'migration'
            if key not in meta:
                continue  # XXX warn
            if meta[key] is None:
                meta[key] = frozenset(items)
            # XXX FAIL

    assert meta['name'] is not None
    return Migration(**meta)


def verify_state(state, migrations):
    missing = {}
    for migration in migrations:
        if migration.name in state:
            assert state[migration.name] == migration.checksum
        else:
                missing[migration.name] = migration

    return missing


def pop_next_to_apply(migrations, state):
    for name, item in migrations.items():
        if item.can_apply_on(state):
            return migrations.pop(name)


def missing_migrations(db, migrations):
    state = db.state() or {}
    return verify_state(state, migrations)


def apply_migrations(db, migrations):
    state = db.state() or {}
    missing = missing_migrations(db, migrations)
    print(missing)
    while missing:
        migration = pop_next_to_apply(missing, state)
        db.apply(migration)
        state[migration.name] = migration.checksum
    real_state = db.state()
    if real_state is not None:
        assert state == real_state
    return real_state
