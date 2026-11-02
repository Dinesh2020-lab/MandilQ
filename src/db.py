"""Database engines: admin (ETL) and read-only (assistant). Config from environment only."""
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _url(user_key: str, pw_key: str) -> str:
    return (f"postgresql+psycopg2://{os.environ[user_key]}:{os.environ[pw_key]}"
            f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.environ['POSTGRES_DB']}")


def admin_engine() -> Engine:
    return create_engine(_url("ADMIN_USER", "ADMIN_PASSWORD"))


def readonly_engine() -> Engine:
    return create_engine(_url("RO_USER", "RO_PASSWORD"),
                         connect_args={"options": "-c statement_timeout=10000 -c default_transaction_read_only=on"})
