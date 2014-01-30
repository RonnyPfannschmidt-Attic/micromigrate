from hashlib import sha256
from collections import namedtuple

Migration = namedtuple('Migration', 'name checksum sql before after')


initial_migration = """
        -- migration micromigrate:enable
        -- before *
        create table micromigrate_migrations (
            id integer primary key,
            name unique,
            checksum,
            completed default null
            );
"""


def parse_migration(sql):
    lines = sql.splitlines()
    meta = {
        'checksum': sha256(sql).hexdigest(),
        'sql': sql,
        'before': None,
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
        if  meta['name'] is None:
            assert items[0] == 'migration', 'first comment must be migration name'
            assert len(items) == 2
            meta['name'] = items[1]
        else:
            assert items[0] != 'migration'
            assert meta[items[0]] is None
            meta[items[0]] = tuple(items[1:])
    assert meta['name'] is not None
    return Migration(**meta)




meta_migrations = [parse_migration(initial_migration)]


def push_migration(connection, state, migration):

    if state:
        connection.execute("""
            insert into micromigrate_migrations (name, checksum)
            values (:name, :checksum)""", migration._asdict())
    connection.execute(migration.sql)
    connection.execute("""
        update micromigrate_migrations
            set completed = 1
            where name = :name
        """, migration._asdict())
    state = state.copy()
    state[migration.name] = migration.checksum
    return state


def migration_state(connection):
    try:
        result = connection.execute("""
           select name, hash
           from minimal_migrations
        """)
    except Exception:
        return {}
    else:
        return dict(result)


def verify_state(state, migrations):
    missing = []
    for migration in migrations:
        if migration.name in state:
            assert state[migration.name] == migration.checksum
        else:
            missing.append(migration)

    return missing


def migrate(connection, migrations):
    all_migrations = meta_migrations + migrations
    state = migration_state(connection)
    missing_migrations = verify_state(state, all_migrations)
    for migration in missing_migrations:
        state = push_migration(connection, state, migration)
    return state
