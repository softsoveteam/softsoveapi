from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://softsove.vercel.app,https://softsove.com,https://www.softsove.com"
    cors_origin_regex: str = r"https://([a-z0-9-]+\.)?softsove\.com|https://softsove\.vercel\.app"
    upload_dir: str = "uploads/cvs"
    database_url: str = "sqlite:///./data/softsove.db"
    secret_key: str = "change-this-secret-key"

    contact_to_email: str = ""
    contact_from_name: str = "Softsove"
    contact_from_email: str = ""
    contact_subject: str = "Message from Softsove"
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_secure: bool = True
    smtp_user: str = ""
    smtp_pass: str = ""

    def sqlalchemy_url(self) -> str:
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg2://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg2://" + url[len("postgresql://") :]
        if url.startswith("sqlite:///"):
            raw = url[len("sqlite:///") :]
            path = Path(raw)
            if not path.is_absolute():
                path = (ROOT / path).resolve()
                url = "sqlite:///" + path.as_posix()
        return url


settings = Settings()
