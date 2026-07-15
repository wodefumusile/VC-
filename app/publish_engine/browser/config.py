from __future__ import annotations

import os
"""Browser config v3.0 - CDP mode support"""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

WECHAT_MP_URL = "https://mp.weixin.qq.com"
WECHAT_HOME_URL = "https://mp.weixin.qq.com/cgi-bin/home"
WECHAT_EDITOR_URL_BASE = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77&isMul=1"
MATERIAL_LIST_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_list&action=list&type=77"

# CDP mode: connect to existing Chrome (in-app browser)
BROWSER_CDP_URL = os.environ.get("BROWSER_CDP_URL", "http://localhost:9229")

_session_token = None

def set_token(token: str):
    global _session_token
    _session_token = token

def get_token() -> str | None:
    return _session_token

def get_home_url() -> str:
    token = get_token()
    if token:
        return f"https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token={token}"
    return WECHAT_HOME_URL

def get_editor_url() -> str:
    token = get_token()
    url = WECHAT_EDITOR_URL_BASE
    if token:
        url += f"&token={token}&lang=zh_CN"
    return url

def get_material_list_url() -> str:
    token = get_token()
    url = MATERIAL_LIST_URL
    if token:
        url += f"&token={token}&lang=zh_CN"
    return url

USER_DATA_DIR = Path(os.environ.get("USERPROFILE", ".")) / "wechat_browser_profile"
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"

BROWSER_CONFIG = {
    "headless": False,
    "viewport": {"width": 1280, "height": 800},
    "locale": "zh-CN",
}

LOGIN_TIMEOUT = 300
PAGE_TIMEOUT = 30000
