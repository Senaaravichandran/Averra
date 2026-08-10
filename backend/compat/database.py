"""Backward-compatible database helpers.

New code should import from ``averra.db`` and pass an explicit database path.
"""

from config import DATABASE_PATH
from backend.averra.db import get_db as _get_db, init_db as _init_db, rows_to_dict


def get_db():
    return _get_db(DATABASE_PATH)


def init_db():
    return _init_db(DATABASE_PATH)
