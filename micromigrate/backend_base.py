
HAS_MIGRATIONS = '''
    select name, type
    from sqlite_master
    where type = "table"
    and name = "micromigrate_migrations"
'''

MIGRATIONS_AND_CHECKSUMS = """
    select
        name,
        case
            when completed = 1
            then checksum
            else ':failed to complete'
        end as checksum
    from micromigrate_migrations
"""


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
