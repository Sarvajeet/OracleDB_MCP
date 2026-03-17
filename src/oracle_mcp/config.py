"""Configuration for Oracle MCP Server, loaded from environment variables / .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class OracleSettings(BaseSettings):
    """Oracle Database connection settings.

    Values are read from environment variables (prefixed with ORACLE_)
    or from a .env file in the working directory.
    """

    model_config = SettingsConfigDict(
        env_prefix="ORACLE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connection parameters
    host: str = "localhost"
    port: int = 1521
    service: str = "FREEPDB1"
    user: str = "system"
    password: str = ""

    # Optional: full DSN override (takes precedence over host/port/service)
    dsn: str | None = None

    # Connection pool sizing
    min_pool: int = 1
    max_pool: int = 5

    # Safety
    readonly: bool = False  # If True, DML and DDL tools are disabled
    max_rows: int = 500  # Default row limit for queries

    @property
    def connect_dsn(self) -> str:
        """Return the DSN string for oracledb connection."""
        if self.dsn:
            return self.dsn
        return f"{self.host}:{self.port}/{self.service}"


class ServerSettings(BaseSettings):
    """MCP server transport settings."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    transport: str = "stdio"  # "stdio" or "sse"
    sse_host: str = "0.0.0.0"
    sse_port: int = 8000


# Singleton instances
oracle_settings = OracleSettings()
server_settings = ServerSettings()


