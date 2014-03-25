import pytest

from micromigrate.backend_script import ScriptBackend
from micromigrate.backend_pysqlite import PySqliteBackend


backends = {
    'script': ScriptBackend,
    'binding': PySqliteBackend,
}

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


@pytest.fixture(params=sorted(backends.keys()))
def db(request, dbname):
    return backends[request.param](dbname)


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, __multicall__):
    report = __multicall__.execute()
    dbname = getattr(item, '_dbname', None)
    if dbname is not None:
        from micromigrate.util import output_or_raise
        try:
            report.sections.append(
                ('db', output_or_raise('sqlite3', '.dump', dbname)))
        except:
            pass
    return report
