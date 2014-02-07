from .constants import (
    HAS_MIGRATIONS,
    MIGRATIONS_AND_CHECKSUMS,
)


class BackendBase(object):

    def run_query(self, query):
        raise NotImplementedError

    def state(self):
        result = self.run_query(HAS_MIGRATIONS)
        if result:
            return {
                row['name']: row['checksum']
                for row in self.run_query(MIGRATIONS_AND_CHECKSUMS)
            }
