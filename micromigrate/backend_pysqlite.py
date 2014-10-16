import sqlite3

from .backend_base import BackendBase
from sqlparse import split


class PySqliteBackend(BackendBase):

    def __init__(self, connection):
        self.connection = connection

    @classmethod
    def from_path(cls, dbname):
        connection = sqlite3.connect(str(dbname), isolation_level=None)
        connection.row_factory = sqlite3.Row
        return cls(connection)

    def run_script(self, script):
        c = self.connection.cursor()
        try:
            for statement in split(script):
                c.execute(statement)
            c.close()
        except:
            c.execute('rollback')
            c.close()
            raise

    def run_query(self, query):
        c = self.connection.cursor()
        return c.execute(query).fetchall()
