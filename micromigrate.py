from __future__ import print_function
from hashlib import sha256
from collections import namedtuple


class Migration(namedtuple('MigrationBase', 'name checksum sql after')):
    __slots__ = ()

    def __repr__(self):
        return '<Migration {name} ck {checksum}..>'.format(
            name=self.name,
            checksum=self.checksum[:6],
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


initial_migration = parse_migration(u"""
        -- migration micromigrate:enable
        create table micromigrate_migrations (
            id integer primary key,
            name unique,
            checksum,
            completed default 0
            );
""")


def _prepare_migration(connection, migration, first):
    if not first:
        connection.execute("""
            insert into micromigrate_migrations (name, checksum)
            values (:name, :checksum)""", migration._asdict())


def _record_migration_result(connection, migration, first):
    if not first:
        c = connection.execute("""
            update micromigrate_migrations
                set completed = 1
                where name = :name;
            """, migration._asdict())
    else:
        c = connection.execute("""
            insert into micromigrate_migrations (name, checksum, completed)
            values (:name, :checksum, 1);""", migration._asdict())
    assert c.rowcount == 1


def push_migration(connection, migration, first):
    print('migration', migration.name)
    _prepare_migration(connection, migration, first)
    try:
        connection.executescript(migration.sql)
    except connection.Error as error:
        print(' ', error)
    else:
        _record_migration_result(connection, migration, first)



def migration_state(connection):
    c = connection.execute("""
        select name, type
        from sqlite_master
        where type = "table"
        and name = "micromigrate_migrations";
    """)
    items = list(c)
    if items:
        return dict(connection.execute("""
            select
                name,
                case
                    when completed = 1
                    then checksum
                    else ':failed to complete'
                end
            from micromigrate_migrations
        """))


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
        if mig.after is None or not (names & mig.after)
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
    if state is None:
        state = {}
        missing_migrations = all_migrations
    else:
        missing_migrations = verify_state(state, all_migrations)

    for migration in iter_next_doable(missing_migrations):
        assert can_do(migration, state)
        push_migration(connection, migration, first=not state)
        state[migration.name] = migration.checksum
    return migration_state(connection)
