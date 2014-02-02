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


MIGRATION_SCRIPT="""
begin transaction;;

create table if not exists micromigrate_migrations (
    id integer primary key,
    name unique,
    checksum,
    completed default 0
    );


insert into micromigrate_migrations (name, checksum)
values ("{migration.name}", "{migration.checksum}");

select 'executing' as status;

{migration.sql}
;
select 'finalizing' as stats;

update micromigrate_migrations
set completed = 1
where name = "{migration.name}";

select 'commiting' as status, "{migration.name}" as migration;

commit;
"""

def runsqlite(dbname, script):
    subprocess.check_call([
        'sqlite3', '-line',
        str(dbname), script,
    ])

def runquery(dbname, query):
    proc = subprocess.Popen(
        ['sqlite3', '-line', str(dbname), query],
        stdout = subprocess.PIPE,
        universal_newlines=True,
    )
    out, ignored = proc.communicate()
    if proc.returncode:
        raise Exception(proc.returncode)
    
    chunks = out.split('\n\n')
    return [
        dict(x.strip().split(' = ') for x in chunk.splitlines())
        for chunk in chunks if chunk.strip()
    ]


def push_migration(dbname, migration):
    script = MIGRATION_SCRIPT.format(migration=migration)
    try:
        runsqlite(dbname, script)
    except subprocess.CalledProcessError:
        pass
    return migration_state(dbname)

def migration_state(dbname):
    proc = '''select name, type
        from sqlite_master
        where type = "table"
        and name = "micromigrate_migrations"
    '''
    listit = """select
                name,
                case
                    when completed = 1
                    then checksum
                    else ':failed to complete'
                end as checksum
            from micromigrate_migrations
        """
    result = runquery(dbname, proc)
    if result:
        return dict(
            (row['name'], row['checksum'])
            for row in runquery(dbname, listit))



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
    return (
        migration.after is None or
        not any(name not in state for name in migration.after)
    )


def apply_migrations(dbname, migrations):
    # we put our internal migrations behind the given ones intentionally
    # this requires that people depend on our own migrations
    # in order to have theirs work
    state = migration_state(dbname) or {}
    missing_migrations = verify_state(state, migrations)

    for migration in iter_next_doable(missing_migrations):
        assert can_do(migration, state)
        push_migration(dbname, migration)
        state[migration.name] = migration.checksum
    return migration_state(dbname)
