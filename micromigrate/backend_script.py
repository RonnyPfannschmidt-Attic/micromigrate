"""
    migration backend using the sqlite command

    supports transactional migrations
"""

from .backend_base import BackendBase
from .util import parse_lineoutput, output_or_raise


class ScriptBackend(BackendBase):
    def __init__(self, dbname):
        self.dbname = dbname

    def __repr__(self):
        return '<ScriptBackend %r>' % (self.dbname,)
    
    def run_script(self, script):
        self.run_query(script)

    def run_query(self, query):
        out = output_or_raise(
            'sqlite3', '-line',
            str(self.dbname), query,
        )
        return parse_lineoutput(out)
