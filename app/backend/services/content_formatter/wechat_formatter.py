"""WeChat formatting engine - unified entry"""

from loguru import logger
from .formatter_rules import format_article as _format_article
from .style_templates import get_template, get_all_templates, get_prompt_instructions


def format_article(title, content, author="", template="knowledge"):
    """Format article for WeChat editor"""
    logger.info("format start | template={} | title_len={} | body_len={}",
                template, len(title), len(content))
    result = _format_article(title, content, author, template)
    logger.success("format done | template={} | html_len={}", template, len(result["content_html"]))
    return result
