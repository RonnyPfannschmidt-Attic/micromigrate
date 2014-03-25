import sqlite3

from .backend_base import BackendBase
from .constants import MIGRATION_SCRIPT
from .types import MigrationError
from sqlparse import split

class PySqliteBackend(BackendBase):
    def __init__(self, dbname):
        self.connection = sqlite3.connect(str(dbname), isolation_level=None)
        self.connection.row_factory = sqlite3.Row

    def run_script(self, script):
        c = self.connection.cursor()
        try:
            for statement in split(script):
                c.execute(statement);
        except:
            c.execute('rollback')
            raise
    def run_query(self, query):
        c = self.connection.cursor()
        return c.execute(query).fetchall()
