"""Set safe defaults for the unauthenticated service-level test suite."""

import os


def pytest_configure():
    os.environ["AUTH_REQUIRED"] = "false"
