# Program by Kaliyev.A
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_token: str
    openai_api_key: str | None
    openai_model: str
    db_path: str

    project_name: str
    event_desc: str
    audience: str
    benefits: str
    ask_amount: str
    language: str


def _require_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(name)
    return val


def load_config() -> Config:
    load_dotenv()

    telegram_token = _require_env("TELEGRAM_TOKEN")
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    db_path = os.getenv("DB_PATH", "data/app.db").strip()

    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    return Config(
        telegram_token=telegram_token,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        db_path=db_path,
        project_name=os.getenv("PROJECT_NAME", "SponsoBot").strip(),
        event_desc=os.getenv("EVENT_DESC", "").strip(),
        audience=os.getenv("AUDIENCE", "").strip(),
        benefits=os.getenv("BENEFITS", "").strip(),
        ask_amount=os.getenv("ASK_AMOUNT", "").strip(),
        language=os.getenv("LANGUAGE", "ru").strip().lower(),
    )
