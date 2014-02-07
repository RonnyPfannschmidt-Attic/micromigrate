"""
    migration backend using the sqlite command

    supports transactional migrations
"""
import subprocess

from .backend_base import BackendBase


MIGRATION_SCRIPT = """
begin transaction;

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


def runquery(dbname, query):
    proc = subprocess.Popen(
        ['sqlite3', '-line', str(dbname), query],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    out, ignored = proc.communicate()
    if proc.returncode:
        raise Exception(proc.returncode, out, ignored)

    chunks = out.split('\n\n')
    return [
        dict(x.strip().split(' = ') for x in chunk.splitlines())
        for chunk in chunks if chunk.strip()
    ]

def runsqlite(dbname, script):
    subprocess.check_call([
        'sqlite3', '-line',
        str(dbname), script,
    ])


class MigrationError(Exception):
    pass


class ScriptBackend(BackendBase):
    def __init__(self, dbname):
        self.dbname = dbname

    def __repr__(self):
        return '<scriptbackend %r>' % (self.dbname,)


    def apply(self, migration):
        script = MIGRATION_SCRIPT.format(migration=migration)
        try:
            runsqlite(self.dbname, script)
        except subprocess.CalledProcessError:
            raise MigrationError('migration failed')

    def run_query(self, query):
        return runquery(self.dbname, query)

    def run_script(self, script):
        runsqlite(self.dbname, script)

    def results(self, query, params):
        assert not params, 'params unsupported'
        return runquery(self.dbname, query)

