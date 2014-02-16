import pytest


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
