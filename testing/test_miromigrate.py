import pytest
from micromigrate import migrate, migration_state, parse_migration


@pytest.fixture
def plain_conn():
    import sqlite3
    return sqlite3.connect(':memory:')


def test_parse_migration():
    result = parse_migration("-- migration test")
    assert result.name == 'test'
    pytest.raises(AssertionError,
                  parse_migration, "")

    pytest.raises(AssertionError,
                  parse_migration, "-- not named")
    result = parse_migration("-- migration test\n"
                             "-- before fun")
    assert result.name == 'test'
    assert result.before == ('fun',)


def test_migration_initial(plain_conn):
    state = migration_state(plain_conn)
    assert state == {}
    new_state = migrate(plain_conn, [])
    assert 'micromigrate:enable' in new_state

