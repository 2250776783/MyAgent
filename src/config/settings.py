from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="DEEPSEEK_BASE_URL")
    llm_model: str = "deepseek-v4-flash"

    embed_api_key: str = Field(default="", alias="EMBED_API_KEY")
    embed_base_url: str = Field(default="", alias="EMBED_BASE_URL")
    embed_model: str = "text-embedding-3-small"

    serpapi_api_key: str = Field(default="", alias="SERPAPI_API_KEY")

    chroma_path: str = "./chroma_db"

    # ─── PostgreSQL ────────────────────────────────────────────────────
    pg_host: str = Field(default="localhost", alias="PG_HOST")
    pg_port: int = Field(default=5432, alias="PG_PORT")
    pg_user: str = Field(default="myagent", alias="PG_USER")
    pg_password: str = Field(default="myagent_secret", alias="PG_PASSWORD")
    pg_database: str = Field(default="agent_memory", alias="PG_DATABASE")
    pg_min_size: int = Field(default=2, alias="PG_MIN_SIZE")
    pg_max_size: int = Field(default=10, alias="PG_MAX_SIZE")

    # ─── Redis ─────────────────────────────────────────────────────────
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    @property
    def pg_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def pg_sync_dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
