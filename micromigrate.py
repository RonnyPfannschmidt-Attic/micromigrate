from hashlib import sha256
from collections import namedtuple

Migration = namedtuple('Migration', 'name checksum sql after')


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


initial_migration = parse_migration(u"""
        -- migration micromigrate:enable
        create table micromigrate_migrations (
            id integer primary key,
            name unique,
            checksum,
            completed default 0
            );
""")


def push_migration(connection, state, migration):

    if state:
        connection.execute("""
            insert into micromigrate_migrations (name, checksum)
            values (:name, :checksum)""", migration._asdict())
    connection.execute(migration.sql)
    if state:
        c = connection.execute("""
            update micromigrate_migrations
                set completed = 1
                where name = :name
            """, migration._asdict())
    else:
        c = connection.execute("""
            insert into micromigrate_migrations (name, checksum, completed)
            values (:name, :checksum, 1)""", migration._asdict())
    assert c.rowcount == 1
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


def pick_next_doable(migrations):
    names = set(x.name for x in migrations)

    migrations = [
        mig for mig in migrations
        if mig.after is None or not (mig.after - names)
    ]
    return migrations[0]


def iter_next_doable(migrations):
    while migrations:
        next_migration = pick_next_doable(migrations)
        yield next_migration
        migrations.remove(next_migration)


def can_do(migration, state):
    if not state:
        assert migration is initial_migration, \
            'first migration must depend on %s' % initial_migration.name
    return (
        migration.after is None or
        not any(name not in state for name in migration.after)
    )


def migrate(connection, migrations):
    # we put our internal migrations behind the given ones intentionally
    # this requires that people depend on our own migrations
    # in order to have theirs work
    all_migrations = migrations + [initial_migration]
    state = migration_state(connection)
    missing_migrations = verify_state(state, all_migrations)

    for migration in iter_next_doable(missing_migrations):
        assert can_do(migration, state)
        state = push_migration(connection, state, migration)
    return state
