
import pytest


def pytest_addoption(parser):
    parser.addoption('--skip-ost', action='store_true', default=False)
