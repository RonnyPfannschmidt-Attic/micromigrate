from collections import namedtuple


class Migration(namedtuple('MigrationBase', 'name checksum sql after')):
    __slots__ = ()

    def __repr__(self):
        return '<Migration {name} ck {checksum}..>'.format(
            name=self.name,
            checksum=self.checksum[:6],
        )

    def can_apply_on(self, state):
        return (
            self.after is None or
            not any(name not in state for name in self.after)
        )


class MigrationError(Exception):
    pass
