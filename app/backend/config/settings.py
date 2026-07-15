"""
统一配置管理

优先 .env → 环境变量 → 默认值
所有配置通过此模块访问，禁止硬编码。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env（项目根目录）
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    """应用配置（单例模式）"""

    # --- 应用 ---
    APP_NAME: str = os.getenv("APP_NAME", "wechat-ai-publisher")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.1.3")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # --- 安全 ---
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")

    # --- 发布模式 ---
    CLIENT_MODE: bool = os.getenv("CLIENT_MODE", "true").lower() in ("true", "1", "yes")
    PUBLISH_MODE: str = os.getenv("PUBLISH_MODE", "auto")  # auto | manual

    # --- 服务器 ---
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # --- 日志 ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ROOT_DIR: Path = ROOT_DIR
    LOG_DIR: Path = ROOT_DIR / "logs"

    # --- AI API ---
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek-chat")

    # --- 图片生成 Provider（v2.0）---
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "jimeng")  # jimeng | openai
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_BASE_URL: str = os.getenv("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "doubao-seedream-4-0")

    # --- 知识库 (Obsidian) ---
    OBSIDIAN_PATH: str = os.getenv("OBSIDIAN_PATH", "")

    # --- 模块开关 ---
    ENABLE_AI_GENERATE: bool = os.getenv("ENABLE_AI_GENERATE", "true").lower() in ("true", "1", "yes")
    ENABLE_KNOWLEDGE: bool = os.getenv("ENABLE_KNOWLEDGE", "true").lower() in ("true", "1", "yes")
    ENABLE_IMAGE: bool = os.getenv("ENABLE_IMAGE", "true").lower() in ("true", "1", "yes")

    # --- n8n ---
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

    # --- 通知 ---
    APPRISE_DINGTALK: str = os.getenv("APPRISE_DINGTALK", "")
    APPRISE_FEISHU: str = os.getenv("APPRISE_FEISHU", "")
    APPRISE_TELEGRAM: str = os.getenv("APPRISE_TELEGRAM", "")
    APPRISE_EMAIL: str = os.getenv("APPRISE_EMAIL", "")

    # --- 目录 ---
    DATABASE_DIR: Path = ROOT_DIR / "storage"
    STORAGE_DIR: Path = ROOT_DIR / "storage"
    KNOWLEDGE_DIR: Path = ROOT_DIR / "knowledge"
    PROMPTS_DIR: Path = ROOT_DIR / "prompts"
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def obsidian_enabled(self) -> bool:
        """OBSIDIAN_PATH 为空时自动跳过知识库"""
        return bool(self.OBSIDIAN_PATH) and self.ENABLE_KNOWLEDGE

    @property
    def image_enabled(self) -> bool:
        """IMAGE_API_KEY 为空时自动跳过图片生成"""
        return bool(self.IMAGE_API_KEY) and self.ENABLE_IMAGE


# 全局单例
settings = Settings()


def reload_settings():
    """Hot-reload key settings from .env without restarting.
    Uses os.environ override so all modules pick up changes immediately."""
    import os as _os
    from pathlib import Path as _Path

    _env_path = _Path(__file__).resolve().parent.parent.parent / ".env"
    if not _env_path.exists():
        _env_path = ROOT_DIR / ".env"

    if not _env_path.exists():
        return

    # Read .env and update os.environ (pydantic-settings reads from env)
    _keys = [
        "AI_API_KEY", "AI_BASE_URL", "AI_MODEL",
        "IMAGE_PROVIDER", "IMAGE_API_KEY", "IMAGE_BASE_URL", "IMAGE_MODEL",
        "OBSIDIAN_PATH",
        "ENABLE_AI_GENERATE", "ENABLE_KNOWLEDGE", "ENABLE_IMAGE",
        "PUBLISH_MODE", "ADMIN_TOKEN", "CLIENT_MODE",
        "LOG_LEVEL", "SERVER_HOST", "SERVER_PORT",
    ]
    updated = 0
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                if key in _keys:
                    _os.environ[key] = val.strip()
                    updated += 1
    print(f"[Settings] Hot-reloaded {updated} keys from .env")

    # Also reset the model_client singleton to pick up new keys
    try:
        from backend.services.ai.model_client import model_client
        model_client.reset_client()
        print("[Settings] ModelClient reset with new keys")
    except Exception as e:
        print(f"[Settings] ModelClient reset warning: {e}")



class Settings:
    """应用配置（单例模式）"""

    # --- 应用 ---
    APP_NAME: str = os.getenv("APP_NAME", "wechat-ai-publisher")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.1.3")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    # --- 安全 ---
    ADMIN_TOKEN: str = os.getenv("ADMIN_TOKEN", "")

    # --- 发布模式 ---
    CLIENT_MODE: bool = os.getenv("CLIENT_MODE", "true").lower() in ("true", "1", "yes")
    PUBLISH_MODE: str = os.getenv("PUBLISH_MODE", "auto")  # auto | manual

    # --- 服务器 ---
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    # --- 日志 ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ROOT_DIR: Path = ROOT_DIR
    LOG_DIR: Path = ROOT_DIR / "logs"

    # --- AI API ---
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek-chat")

    # --- 图片生成 Provider（v2.0）---
    IMAGE_PROVIDER: str = os.getenv("IMAGE_PROVIDER", "jimeng")  # jimeng | openai
    IMAGE_API_KEY: str = os.getenv("IMAGE_API_KEY", "")
    IMAGE_BASE_URL: str = os.getenv("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "doubao-seedream-4-0")

    # --- 知识库 (Obsidian) ---
    OBSIDIAN_PATH: str = os.getenv("OBSIDIAN_PATH", "")

    # --- 模块开关 ---
    ENABLE_AI_GENERATE: bool = os.getenv("ENABLE_AI_GENERATE", "true").lower() in ("true", "1", "yes")
    ENABLE_KNOWLEDGE: bool = os.getenv("ENABLE_KNOWLEDGE", "true").lower() in ("true", "1", "yes")
    ENABLE_IMAGE: bool = os.getenv("ENABLE_IMAGE", "true").lower() in ("true", "1", "yes")

    # --- n8n ---
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

    # --- 通知 ---
    APPRISE_DINGTALK: str = os.getenv("APPRISE_DINGTALK", "")
    APPRISE_FEISHU: str = os.getenv("APPRISE_FEISHU", "")
    APPRISE_TELEGRAM: str = os.getenv("APPRISE_TELEGRAM", "")
    APPRISE_EMAIL: str = os.getenv("APPRISE_EMAIL", "")

    # --- 目录 ---
    DATABASE_DIR: Path = ROOT_DIR / "storage"
    STORAGE_DIR: Path = ROOT_DIR / "storage"
    KNOWLEDGE_DIR: Path = ROOT_DIR / "knowledge"
    PROMPTS_DIR: Path = ROOT_DIR / "prompts"
    TEMPLATES_DIR: Path = Path(__file__).resolve().parent.parent / "templates"

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_prod(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def obsidian_enabled(self) -> bool:
        """OBSIDIAN_PATH 为空时自动跳过知识库"""
        return bool(self.OBSIDIAN_PATH) and self.ENABLE_KNOWLEDGE

    @property
    def image_enabled(self) -> bool:
        """IMAGE_API_KEY 为空时自动跳过图片生成"""
        return bool(self.IMAGE_API_KEY) and self.ENABLE_IMAGE


# 全局单例
settings = Settings()
