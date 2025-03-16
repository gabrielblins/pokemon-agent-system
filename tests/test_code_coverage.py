"""
Test file for setting up code coverage with pytest-cov.

Run with:
pytest --cov=app tests/ --cov-report=term-missing --cov-report=xml:coverage.xml
"""


def test_ensure_coverage_runs():
    """
    This is a dummy test to ensure pytest-cov can run.

    The actual coverage is determined by running all tests with the --cov flag.
    """
    assert True
