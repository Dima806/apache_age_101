"""Typed settings loaded from config/settings.yaml (DB fields also read env)."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = REPO_ROOT / "config" / "settings.yaml"


class DBSettings(BaseSettings):
    """Local Postgres connection. Overridable via AGE_DB_* environment vars."""

    model_config = SettingsConfigDict(env_prefix="AGE_DB_", extra="ignore")

    host: str = "localhost"
    port: int = 5432
    dbname: str = "age101"
    user: str = "postgres"
    password: str = "postgres"
    connect_timeout: int = 3

    @property
    def conninfo(self) -> str:
        """libpq connection string for psycopg."""
        return (
            f"host={self.host} port={self.port} dbname={self.dbname} "
            f"user={self.user} password={self.password} "
            f"connect_timeout={self.connect_timeout}"
        )


class GraphNames(BaseModel):
    """Names of the AGE graphs this project creates."""

    social: str = "social_txn"
    copurchase: str = "copurchase"
    dependency: str = "dependency"
    knowledge: str = "knowledge"


class DatasetSettings(BaseModel):
    """Sizes and seeds for the synthetic, planted-truth graphs."""

    seed: int = 7
    n_accounts: int = 400
    n_users: int = 200
    n_items: int = 120
    n_components: int = 150
    n_communities: int = 6
    n_rings: int = 6
    ring_min_len: int = 3
    ring_max_len: int = 5
    avg_knows_degree: int = 4
    avg_pays_degree: int = 3


class Settings(BaseModel):
    """Top-level project settings."""

    db: DBSettings = Field(default_factory=DBSettings)
    graphs: GraphNames = Field(default_factory=GraphNames)
    dataset: DatasetSettings = Field(default_factory=DatasetSettings)


def load_settings(path: Path | None = None) -> Settings:
    """Load settings from YAML, falling back to defaults when the file is absent."""
    path = path or DEFAULT_SETTINGS_PATH
    if not path.exists():
        return Settings()
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    return Settings.model_validate(data)
