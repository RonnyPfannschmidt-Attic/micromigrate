import pytest
import micromigrate as mm

@pytest.fixture
def plain_conn(request):
    import sqlite3
    conn = sqlite3.connect(':memory:')
    request._pyfuncitem._conn = conn
    return conn


@pytest.fixture
def conn(plain_conn):
    mm.migrate(plain_conn, [])
    return plain_conn


def print_db(conn):
    print('\n'.join(conn.iterdump()))


def test_parse_migration():
    result = mm.parse_migration("-- migration test")
    assert result.name == 'test'
    pytest.raises(AssertionError,
                  mm.parse_migration, "")

    pytest.raises(AssertionError,
                  mm.parse_migration, "-- not named")
    result = mm.parse_migration(
        "-- migration test\n"
        "-- after fun")
    assert result.name == 'test'
    assert result.after == frozenset(('fun',))


def test_migration_initial(plain_conn):
    state = mm.migration_state(plain_conn)
    assert state is None
    new_state = mm.migrate(plain_conn, [])
    assert 'micromigrate:enable' in new_state


def test_migrate_missing_dep_breaks(plain_conn):
    migration = mm.parse_migration("""
        -- migration test
        create table test(id, name);
    """)
    info = pytest.raises(
        AssertionError, mm.migrate,
        plain_conn, [migration])
    assert info.value.args[0].startswith('first migration must')


def test_migration_state(plain_conn):
    assert mm.migration_state(plain_conn) is None
    plain_conn.execute(mm.initial_migration.sql)
    assert mm.migration_state(plain_conn) == {}
    mm._record_migration_result(plain_conn, mm.initial_migration, True)
    assert mm.migration_state(plain_conn) == {
        mm.initial_migration.name: mm.initial_migration.checksum,
    }


def test_boken_transaction(conn):
    state = mm.migration_state(conn)
    print('state', sorted(state))
    migration = mm.parse_migration(u"""
        -- migration broke
        -- after micromigrate:enable
        create table foo(name unique);
        insert into foo values ('a');
        insert into foo values ('a');
        """)
    print(migration, migration.after)
    mm.migrate(conn, [migration])
    state = mm.migration_state(conn)
    assert state[migration.name] == ':failed to complete'
