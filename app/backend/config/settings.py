"""
Unified configuration — .env → env vars → defaults.
All config goes through this module; no hardcoding.
Supports PyInstaller (_MEIPASS) for packaged builds.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---- PyInstaller support ----
# _MEIPASS is the temp dir where PyInstaller unpacks bundled files (read-only).
# When not frozen, fall back to the source tree.
if getattr(sys, "frozen", False):
    _BUNDLE_DIR = Path(sys._MEIPASS)        # read-only: prompts, templates
    _EXE_DIR = Path(sys.executable).parent  # writable: .env, logs, storage
else:
    _BUNDLE_DIR = Path(__file__).resolve().parent.parent.parent
    _EXE_DIR = _BUNDLE_DIR

# Load .env from writable dir (next to exe, or app/ in dev)
_ENV_PATH = _EXE_DIR / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv(_BUNDLE_DIR / ".env")


class Settings:
    """Application config (singleton)"""

    # ---- App ----
    APP_NAME: str = os.getenv("APP_NAME", "wechat-ai-publisher")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.2.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # ---- Security ----
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")

    # ---- Publish mode ----
    CLIENT_MODE: bool = os.getenv("CLIENT_MODE", "true").lower() in ("true", "1", "yes")
    PUBLISH_MODE: str = os.getenv("PUBLISH_MODE", "auto")  # auto | manual

    # ---- Server ----
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # ---- Logging ----
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ---- AI API ----
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek-chat")

    # ---- Image generation ----
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "jimeng")
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_BASE_URL: str = os.getenv("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "doubao-seedream-4-0")

    # ---- Knowledge base (Obsidian) ----
    OBSIDIAN_PATH: str = os.getenv("OBSIDIAN_PATH", "")

    # ---- Feature toggles ----
    ENABLE_AI_GENERATE: bool = os.getenv("ENABLE_AI_GENERATE", "true").lower() in ("true", "1", "yes")
    ENABLE_KNOWLEDGE: bool = os.getenv("ENABLE_KNOWLEDGE", "true").lower() in ("true", "1", "yes")
    ENABLE_IMAGE: bool = os.getenv("ENABLE_IMAGE", "true").lower() in ("true", "1", "yes")

    # ---- n8n ----
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

    # ---- Notifications ----
    APPRISE_DINGTALK: str = os.getenv("APPRISE_DINGTALK", "")
    APPRISE_FEISHU: str = os.getenv("APPRISE_FEISHU", "")
    APPRISE_TELEGRAM: str = os.getenv("APPRISE_TELEGRAM", "")
    APPRISE_EMAIL: str = os.getenv("APPRISE_EMAIL", "")

    # ---- Directory paths ----
    # Read-only (bundled in exe): prompts, templates
    BUNDLE_DIR: Path = _BUNDLE_DIR
    PROMPTS_DIR: Path = _BUNDLE_DIR / "prompts"
    TEMPLATES_DIR: Path = _BUNDLE_DIR / "backend" / "templates"

    # Writable (next to exe): logs, storage, db
    EXE_DIR: Path = _EXE_DIR
    LOG_DIR: Path = _EXE_DIR / "logs"
    STORAGE_DIR: Path = _EXE_DIR / "storage"
    DATABASE_DIR: Path = _EXE_DIR / "storage"
    KNOWLEDGE_DIR: Path = _EXE_DIR / "knowledge"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def obsidian_enabled(self) -> bool:
        return bool(self.OBSIDIAN_PATH) and self.ENABLE_KNOWLEDGE

    @property
    def image_enabled(self) -> bool:
        return bool(self.IMAGE_API_KEY) and self.ENABLE_IMAGE


# Global singleton
settings = Settings()


def reload_settings():
    """Hot-reload key settings from .env without restarting."""
    _env_path = _EXE_DIR / ".env"
    if not _env_path.exists():
        _env_path = _BUNDLE_DIR / ".env"
    if not _env_path.exists():
        return

    _loaded = {}
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                _loaded[key] = val.strip()

    # Update os.environ + settings instance attributes
    _bool_keys = {"ENABLE_AI_GENERATE", "ENABLE_KNOWLEDGE", "ENABLE_IMAGE", "CLIENT_MODE"}
    updated = 0
    for key, val in _loaded.items():
        os.environ[key] = val
        if key in _bool_keys:
            val = val.lower() in ("true", "1", "yes")
        elif key in ("SERVER_PORT",):
            val = int(val)
        setattr(settings, key, val)
        updated += 1
    print(f"[Settings] Hot-reloaded {updated} keys from .env")

    try:
        from backend.services.ai.model_client import model_client
        model_client.reset_client()
        print("[Settings] ModelClient reset with new keys")
    except Exception as e:
        print(f"[Settings] ModelClient reset warning: {e}")
