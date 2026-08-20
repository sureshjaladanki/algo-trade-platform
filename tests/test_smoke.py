"""Scaffolding check: the package imports on Python 3.12+."""

import sys

import src


def test_python_version() -> None:
    assert sys.version_info >= (3, 12)


def test_src_imports() -> None:
    assert src.__name__ == "src"
