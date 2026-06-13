"""
Huiyin - Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=True)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class Settings:
    LLM_PROVIDER: str = _env("LLM_PROVIDER", "deepseek")

    DEEPSEEK_API_KEY: str = _env("DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = _env("DEEPSEEK_MODEL", "deepseek-chat")

    GEMINI_API_KEY: str = _env("GEMINI_API_KEY")
    GEMINI_MODEL: str = _env("GEMINI_MODEL", "gemini-3.5-flash")

    MIMO_API_KEY: str = _env("MIMO_API_KEY")
    MIMO_MODEL: str = _env("MIMO_MODEL", "mimo-v2-pro")
    MIMO_BASE_URL: str = _env("MIMO_BASE_URL", "https://api.mimo-v2.com/v1")

    OPENAI_COMPAT_API_KEY: str = _env("OPENAI_COMPAT_API_KEY")
    OPENAI_COMPAT_BASE_URL: str = _env("OPENAI_COMPAT_BASE_URL", "https://api.openai.com/v1")
    OPENAI_COMPAT_MODEL: str = _env("OPENAI_COMPAT_MODEL", "gpt-4o")

    CHANNEL: str = _env("CHANNEL", "cli")
    TELEGRAM_BOT_TOKEN: str = _env("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str = _env("TELEGRAM_CHAT_ID")

    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "./data"))

    @property
    def DB_PATH(self) -> Path:
        return self.DATA_DIR / "huiyin.db"

    @property
    def VECTOR_DB_PATH(self) -> Path:
        return self.DATA_DIR / "vector_db"

    LOG_LEVEL: str = _env("LOG_LEVEL", "INFO")

    def validate(self) -> None:
        key_map = {
            "deepseek": self.DEEPSEEK_API_KEY,
            "gemini": self.GEMINI_API_KEY,
            "mimo": self.MIMO_API_KEY,
            "openai_compat": self.OPENAI_COMPAT_API_KEY,
        }
        if self.LLM_PROVIDER not in key_map:
            raise ValueError(f"Unsupported LLM provider: {self.LLM_PROVIDER}")
        if not key_map[self.LLM_PROVIDER]:
            raise ValueError(
                f"Missing API Key for {self.LLM_PROVIDER}. "
                f"Set {self.LLM_PROVIDER.upper()}_API_KEY in .env"
            )
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
