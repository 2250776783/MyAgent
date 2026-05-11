from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"
    chroma_path: str = "./chroma_db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
