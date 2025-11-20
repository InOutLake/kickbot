from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEFAULT_PASSWORD: str
    DOMAIN: str
    EMAIL_API_PORT: int
    SOCKS_CONNECTION_STRING: str = "socks5://127.0.0.1:9050"

    @property
    def TOR_SOCKS_PROXY(self) -> dict:
        return {"server": self.SOCKS_CONNECTION_STRING}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


SETTINGS = Settings()  # pyright: ignore [reportCallIssue]
