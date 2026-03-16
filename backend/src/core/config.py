"""
应用配置模块

使用 pydantic-settings 管理配置，支持：
- 环境变量覆盖
- .env 文件加载
- YAML 配置文件
- 类型安全验证
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict(env_prefix="DB_")

    # 数据库类型 (sqlite/postgresql/mysql)
    driver: Literal["sqlite", "postgresql", "mysql"] = "sqlite"

    # 连接参数
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "app_db"

    # SQLite 文件路径
    sqlite_file: str = "data/app.db"

    # 连接池配置
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    @property
    def async_url(self) -> str:
        """获取异步数据库连接 URL"""
        if self.driver == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_file}"
        elif self.driver == "postgresql":
            return (
                f"postgresql+asyncpg://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )
        else:
            return (
                f"mysql+aiomysql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )

    @property
    def sync_url(self) -> str:
        """获取同步数据库连接 URL (用于 Alembic)"""
        if self.driver == "sqlite":
            return f"sqlite:///{self.sqlite_file}"
        elif self.driver == "postgresql":
            return (
                f"postgresql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )
        else:
            return (
                f"mysql+pymysql://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.database}"
            )


class RedisSettings(BaseSettings):
    """Redis 配置"""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0

    @property
    def url(self) -> str:
        """获取 Redis 连接 URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class JWTSettings(BaseSettings):
    """JWT 认证配置"""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class LogSettings(BaseSettings):
    """日志配置"""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = "INFO"
    dir: str = "logs"
    rotation: str = "00:00"
    retention: str = "30 days"
    compression: str = "zip"
    enable_console: bool = True
    enable_file: bool = True


class AppSettings(BaseSettings):
    """应用主配置"""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用信息
    name: str = "State Grid Simulator"
    version: str = "1.0.0"
    description: str = "State Grid Simulator Web Application"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # CORS 配置
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    log: LogSettings = Field(default_factory=LogSettings)

    @field_validator("cors_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_list(cls, v):
        """解析 CORS 列表配置"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v


@lru_cache
def get_settings() -> AppSettings:
    """获取应用配置（带缓存）"""
    return AppSettings()


# 全局配置实例
settings = get_settings()


def load_config_from_yaml(config_path: str = "config/config.yaml") -> dict:
    """
    从 YAML 文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    path = Path(config_path)
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}