from __future__ import print_function
from hashlib import sha256
from collections import namedtuple
import subprocess


class Migration(namedtuple('MigrationBase', 'name checksum sql after')):
    __slots__ = ()

    def __repr__(self):
        return '<Migration {name} ck {checksum}..>'.format(
            name=self.name,
            checksum=self.checksum[:6],
        )

    def can_apply_on(self, state):
        return (
            self.after is None or
            not any(name not in state for name in self.after)
        )


def parse_migration(sql):
    """
    parses the metadata of a migration text

    :param sql: text content (unicode on python2) of the migration
    """
    lines = sql.splitlines()
    meta = {
        'checksum': sha256(sql.encode('utf-8')).hexdigest(),
        'sql': sql,
        'after': None,
        'name': None
    }
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('-- '):
            items = line[3:].split()
        else:
            break
        if meta['name'] is None:
            assert items[0] == 'migration', \
                'first comment must be migration name'
            assert len(items) == 2
            meta['name'] = items[1]
        else:
            assert items[0] != 'migration'
            assert meta[items[0]] is None
            meta[items[0]] = frozenset(items[1:])
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


def pop_next_to_apply(migrations):
    takefrom = migrations.copy()
    while takefrom:
        name, item = takefrom.popitem()
        if item.after is None or not any(x in migrations for x in item.after):
            migrations.pop(name)
            return item


def apply_migrations(db, migrations):
    state = db.state() or {}
    missing_migrations = verify_state(state, migrations)

    while missing_migrations:
        migration = pop_next_to_apply(missing_migrations)
        assert migration.can_apply_on(state)
        try:
            db.apply(migration)
        except Exception as e:
            print(migration, 'failed', e)
            break
        state[migration.name] = migration.checksum
    real_state = db.state()
    if real_state is not None:
        assert state == real_state
    return real_state
