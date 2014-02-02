import pytest
from micromigrate import migrate as mm


@pytest.fixture
def dbname(request, tmpdir):
    db = tmpdir.join('test.sqlite.db')
    @request.addfinalizer
    def cleanup():
        import subprocess
        if db.check():
            subprocess.call([
                'sqlite3', str(db), '.dump',
            ])
    return db


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


def test_push_migration(dbname):
    state = mm.migration_state(dbname)
    assert state is None
    migration = mm.parse_migration("""
        -- migration test
        fail
        """)
    mm.push_migration(dbname, migration)
    state = mm.migration_state(dbname)
    assert state is None

    migration = mm.parse_migration("""
        -- migration test
        create table test(name);
        """)
    mm.push_migration(dbname, migration)
    state = mm.migration_state(dbname)
    assert state == {'test': migration.checksum}

def test_migration_initial(dbname):
    state = mm.migration_state(dbname)
    assert state is None
    migration = mm.parse_migration("""
        -- migration test
        create table test(name);
        """)
    new_state = mm.apply_migrations(dbname, [migration])
    assert len(new_state) == 1
    assert new_state[migration.name] == migration.checksum




def test_boken_transaction(dbname):
    migration = mm.parse_migration(u"""
        -- migration broke
        create table foo(name unique);
        insert into foo values ('a');
        insert into foo values ('a');
        """)
    state = mm.apply_migrations(dbname, [migration])
    assert state is None

    migration_working = mm.parse_migration(u"""
        -- migration working
        create table bar(name unique);
        """)

    state = mm.apply_migrations(dbname, [migration_working, migration])
    assert len(state) == 1
    assert state['working'] == migration_working.checksum
