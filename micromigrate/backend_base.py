from .types import MigrationError
import pkg_resources


def _script(name):
    return pkg_resources.resource_string(
        __name__, 'scripts/' + name).decode('utf-8')

HAS_MIGRATIONS = _script('has_migrations.sql')
MIGRATIONS_AND_CHECKSUMS = _script('migrations_and_sums.sql')
MIGRATION_SCRIPT = _script('migration.tpl.sql')


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
