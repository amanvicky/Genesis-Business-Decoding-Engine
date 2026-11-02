from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    genesis_offline: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    genesis_llm_model: str = "llama3.2"
    tor_proxy: str = "socks5://127.0.0.1:9050"
    tor_enabled: bool = True
    request_timeout: int = 25

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
