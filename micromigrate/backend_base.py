from .constants import (
    HAS_MIGRATIONS,
    MIGRATIONS_AND_CHECKSUMS,
)

from .constants import MIGRATION_SCRIPT
from .types import MigrationError

class BackendBase(object):

    def run_query(self, query):
        raise NotImplementedError

    def run_script(self, script):
        raise NotImplementedError


    def apply(self, migration):
        script = MIGRATION_SCRIPT.format(migration=migration)
        try:
            self.run_script(script)
        except Exception as e:
            raise MigrationError(migration.name, e)

    def state(self):
        result = self.run_query(HAS_MIGRATIONS)
        if result:
            return {
                row['name']: row['checksum']
                for row in self.run_query(MIGRATIONS_AND_CHECKSUMS)
            }
