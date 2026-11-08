from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# 以当前文件为基准，找向上2级的父目录，也就是项目的根目录
APP_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # 设置.env文件的路径，默认是项目根目录下的.env
    model_config = SettingsConfigDict(
        env_file=(APP_ROOT / ".env",),
        env_file_encoding="utf-8",
        extra="ignore", # 本类中未定义而.env中出现的字段处理方案
    )
    # 应用信息
    app_name: str = "agent-service"
    app_version: str = "0.1.0"
    # 先去环境配置文件中找配置端口，如果没有则使用默认端口
    app_port: int = Field(default=8002, alias="APP_PORT")

    # 日志级别
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="console", alias="LOG_FORMAT")

    # 虚拟机地址
    infra_host: str | None = Field(default=None, alias="INFRA_HOST")

    # 业务端地址
    business_service_url: str | None = Field(default=None, alias="BUSINESS_SERVICE_URL")

    # 数据库配置
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str | None = Field(default=None, alias="POSTGRES_DB")
    postgres_user: str | None = Field(default=None, alias="POSTGRES_USER")
    postgres_password: str | None = Field(default=None, alias="POSTGRES_PASSWORD")

    # 对话模型
    chat_model: str = Field(default="deepseek-v4-flash", alias="CHAT_MODEL")

    # mineru
    mineru_token: str | None = Field(default=None, alias="MINERU_TOKEN")

    @model_validator(mode="after")
    def derive_infra_urls(self) -> "Settings":
        # 拼接数据库地址
        if self.database_url is None and self.infra_host:
            if self.postgres_db and self.postgres_user and self.postgres_password:
                self.database_url = (
                    "postgresql+asyncpg://"
                    f"{self.postgres_user}:{self.postgres_password}"
                    f"@{self.infra_host}:{self.postgres_port}/{self.postgres_db}"
                )
        # 拼接业务端地址
        if self.business_service_url is None and self.infra_host:
            self.business_service_url = f"http://{self.infra_host}:8001"
        return self

settings = Settings()