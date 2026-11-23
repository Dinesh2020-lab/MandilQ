"""Database engines for local Docker and Render PostgreSQL."""

import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _url() -> str:
    url = os.getenv("DATABASE_URL")

    if url:
        if url.startswith("postgres://"):
            url = url.replace(
                "postgres://", "postgresql+psycopg2://", 1
            )
        elif url.startswith("postgresql://"):
            url = url.replace(
                "postgresql://", "postgresql+psycopg2://", 1
            )
        return url

    return (
        f"postgresql+psycopg2://"
        f"{os.environ['ADMIN_USER']}:{os.environ['ADMIN_PASSWORD']}"
        f"@{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.environ['POSTGRES_DB']}"
    )


def admin_engine() -> Engine:
    return create_engine(_url())


def readonly_engine() -> Engine:
    return create_engine(
        _url(),
        connect_args={
            "options": (
                "-c statement_timeout=10000 "
                "-c default_transaction_read_only=on"
            )
        },
    )
