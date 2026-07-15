"""
Prompt Manager

Loads style-specific prompt templates from prompts/ directory.
"""

from pathlib import Path
from loguru import logger
from backend.config import settings


STYLE_MAP = {
    "marketing": "marketing.txt",
    "science": "science.txt",
    "case_study": "case_study.txt",
    "branding": "branding.txt",
    "seo": "seo.txt",
    "quality_check": "quality_check.txt",
}

SYSTEM_PROMPT = """你是一个微信公众号内容创作专家。你必须严格遵循写作要求生成中文文章。

输出格式必须是纯 JSON（不要 markdown 代码块），结构如下：
{
  "title": "文章标题",
  "summary": "文章摘要（100字以内）",
  "content_html": "HTML格式正文",
  "seo_keywords": "关键词1,关键词2,关键词3"
}

content_html 的严格要求：
- 严禁使用任何内联样式（style="..."）、class、id 属性
- 严禁使用 <section>、<div>、<span> 等容器标签
- 只使用 HTML 标签：<h2>、<p>、<strong>、<blockquote>、<ul>、<li>
- 每个段落必须用 <p> 标签包裹
- 小节标题用 <h2> 标签
- 数字和结论用 <strong> 加粗
- 案例和数据用 <blockquote> 引用
- 严禁在正文中出现（正文）（解释）（标题）等标签文字
- 严禁使用 markdown 格式（##、** 等）
- 直接输出 JSON，不要有任何解释文字"""


class PromptManager:
    def __init__(self, prompts_dir: Path = None):
        self.prompts_dir = prompts_dir or settings.PROMPTS_DIR
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, str] = {}

    def get_available_styles(self) -> list[str]:
        return list(STYLE_MAP.keys())

    def load_prompt(self, style: str) -> str:
        if style not in STYLE_MAP:
            available = ", ".join(self.get_available_styles())
            raise ValueError(f"未知风格 '{style}'，可用: {available}")
        if style in self._cache:
            return self._cache[style]
        filename = STYLE_MAP[style]
        filepath = self.prompts_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"提示词文件不存在: {filepath}")
        content = filepath.read_text(encoding="utf-8")
        self._cache[style] = content
        logger.debug("加载提示词 | style={} | file={}", style, filename)
        return content

    def build_user_prompt(self, style: str, topic: str, length: str = "medium") -> str:
        template = self.load_prompt(style)
        length_map = {"short": "500-800字", "medium": "800-1200字", "long": "1200-1500字"}
        length_desc = length_map.get(length, "800-1200字")
        return template.format(topic=topic, length=length_desc)

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT