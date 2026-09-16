"""Central configuration loaded from .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str


def load_settings(model_override: str | None = None) -> Settings:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Create a .env file with "
            "GEMINI_API_KEY=... (see .env.example)."
        )
    model = (
        (model_override or "").strip()
        or os.getenv("GEMINI_MODEL", "").strip()
        or DEFAULT_MODEL
    )
    return Settings(api_key=api_key, model=model)


def project_root() -> Path:
    return Path(__file__).resolve().parent
