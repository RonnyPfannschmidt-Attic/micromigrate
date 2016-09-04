import pytest

from micromigrate.backend_script import ScriptBackend
from micromigrate.backend_pysqlite import PySqliteBackend

BACKENDS = [
    ScriptBackend,
    PySqliteBackend,
]


@pytest.fixture(params=BACKENDS)
def db(request, tmpdir):
    return request.param.from_path(tmpdir.join('test.sqlite.db').strpath)
