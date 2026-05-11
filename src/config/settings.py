from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="DEEPSEEK_BASE_URL")
    llm_model: str = "deepseek-v4-flash"

    embed_api_key: str = Field(default="", alias="EMBED_API_KEY")
    embed_base_url: str = Field(default="", alias="EMBED_BASE_URL")
    embed_model: str = "text-embedding-3-small"

    chroma_path: str = "./chroma_db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
