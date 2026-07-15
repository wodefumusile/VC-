"""微信公众号 文章数据结构"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class WechatArticle:
    """微信公众号文章"""

    title: str                                    # 标题（必填）
    content: str                                  # 正文HTML（必填）
    summary: str = ""                             # 摘要（可选）
    author: str = "wgzxhhh"                       # 作者，默认 wgzxhhh
    cover_image: Optional[str] = None             # 封面图片路径
    original_flag: bool = False                   # 是否声明原创
    digest: str = ""                              # 引导语

    def to_dict(self) -> dict:
        return asdict(self)

    def validate(self) -> tuple[bool, str]:
        """验证文章数据 — 标题超64字符自动截断，摘要超120字符自动截断"""
        if not self.title or not self.title.strip():
            return False, "标题不能为空"
        if len(self.title) > 64:
            self.title = self.title[:64]
        if not self.content or not self.content.strip():
            return False, "正文不能为空"
        if self.summary and len(self.summary) > 120:
            self.summary = self.summary[:120]
        return True, "ok"