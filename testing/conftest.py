import pytest


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, __multicall__):
    report = __multicall__.execute()
    conn = getattr(item, '_conn', None)
    if conn is not None:
        report.sections.append(('db', '\n'.join(conn.iterdump())))
    return report


