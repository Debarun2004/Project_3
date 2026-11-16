"""Environment-backed application settings."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

APP_NAME = "PrithibiRoute Backend API"
API_VERSION = "1.0.0"

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Settings loaded from environment variables."""

    data_source: str
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    mysql_seed_demo_data: bool


def get_settings() -> Settings:
    """Load settings; MySQL is the runtime default and demo mode is explicit."""
    data_source = os.getenv("DATA_SOURCE", "mysql").strip().lower()
    if data_source not in {"mysql", "demo"}:
        raise ValueError("DATA_SOURCE must be either 'mysql' or 'demo'.")
    return Settings(
        data_source=data_source,
        mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1").strip(),
        mysql_port=int(os.getenv("MYSQL_PORT", "3306")),
        mysql_user=os.getenv("MYSQL_USER", "prithibiroute_app").strip(),
        mysql_password=os.getenv("MYSQL_PASSWORD", ""),
        mysql_database=os.getenv("MYSQL_DATABASE", "prithibiroute").strip(),
        mysql_seed_demo_data=os.getenv("MYSQL_SEED_DEMO_DATA", "true").lower()
        in {"1", "true", "yes", "on"},
    )
