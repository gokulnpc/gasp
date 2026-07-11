"""Runs once before the whole test session: reseeds the DB to a known
state so every test can rely on exactly what's in seed.py. Tests must not
depend on run order or on state left over from manual testing.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import close_driver
import seed


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    seed.run()
    yield
    close_driver()
