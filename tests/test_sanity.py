"""Sanity test — kiểm tra repo được import đúng."""


def test_import_src():
    """src package import được."""
    import src  # noqa: F401


def test_python_version():
    """Python >= 3.10."""
    import sys

    assert sys.version_info >= (3, 10), f"Cần Python 3.10+, hiện tại: {sys.version}"


def test_seed_reproducibility():
    """Cùng seed → cùng random output."""
    import random

    random.seed(42)
    a = [random.random() for _ in range(5)]
    random.seed(42)
    b = [random.random() for _ in range(5)]
    assert a == b
