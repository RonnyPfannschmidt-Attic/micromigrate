"""
    migration backend using the sqlite command

    supports transactional migrations
"""

from .backend_base import BackendBase
from .constants import MIGRATION_SCRIPT
from .types import MigrationError
from .util import parse_lineoutput, output_or_raise


class ScriptBackend(BackendBase):
    def __init__(self, dbname):
        self.dbname = dbname

    def __repr__(self):
        return '<ScriptBackend %r>' % (self.dbname,)

    def apply(self, migration):
        script = MIGRATION_SCRIPT.format(migration=migration)
        try:
            self.run_query(script)
        except Exception as e:
            raise MigrationError('migration failed', e)

    def run_query(self, query):
        out = output_or_raise(
            'sqlite3', '-line',
            str(self.dbname), query,
        )
        return parse_lineoutput(out)
