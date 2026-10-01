"""Database connection from DATABASE_URL (.env). The URL is never printed."""
from __future__ import annotations

import psycopg

from jobfit.config import get_settings


def connect(url: str | None = None) -> psycopg.Connection:
    return psycopg.connect(url or get_settings().database_url, autocommit=False)
