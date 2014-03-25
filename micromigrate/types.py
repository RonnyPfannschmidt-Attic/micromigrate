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


class KWException(Exception):

    def __init__(self, *k, **kw):
        newk = k + (kw,)
        Exception.__init__(self, *newk)


class MigrationError(Exception):
    def __str__(self):
        return "migration `%s` failed: %r" % self.args
