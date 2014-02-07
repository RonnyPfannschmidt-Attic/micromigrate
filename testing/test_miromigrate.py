import pytest
from micromigrate import migrate as mm
from micromigrate.backend_script import ScriptBackend

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

@pytest.fixture
def db(dbname):
    return ScriptBackend(dbname)

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


def test_push_migration(db):
    state = db.state()
    assert state is None
    migration = mm.parse_migration("""
        -- migration test
        fail
        """)
    pytest.raises(Exception, db.apply ,migration)
    state = db.state()
    assert state is None

    migration = mm.parse_migration("""
        -- migration test
        create table test(name);
        """)
    db.apply(migration)
    state = db.state()
    assert state == {'test': migration.checksum}


def test_migration_initial(db):
    state = db.state()
    assert state is None
    migration = mm.parse_migration("""
        -- migration test
        create table test(name);
        """)
    new_state = mm.apply_migrations(db, [migration])
    assert len(new_state) == 1
    assert new_state[migration.name] == migration.checksum


def test_boken_transaction(db):
    migration = mm.parse_migration(u"""
        -- migration broke
        create table foo(name unique);
        insert into foo values ('a');
        insert into foo values ('a');
        """)
    state = mm.apply_migrations(db, [migration])
    assert state is None

    migration_working = mm.parse_migration(u"""
        -- migration working
        create table bar(name unique);
        """)

    state = mm.apply_migrations(db, [migration_working, migration])
    assert len(state) == 1
    assert state['working'] == migration_working.checksum
