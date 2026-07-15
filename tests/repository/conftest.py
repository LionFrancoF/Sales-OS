"""Gemeinsame Fixtures: jede Testfunktion bekommt eine frische tmp-DB."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.config import settings
from src.repository import db


@pytest.fixture(autouse=True)
def tmp_db(tmp_path: Path):
    db.set_db_path(tmp_path / "test.db")
    yield
    db.set_db_path(settings.DB_PATH)
