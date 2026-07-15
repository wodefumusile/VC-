"""Article generator — v2.1.1: improved JSON parsing with Pydantic schema"""

from __future__ import annotations

import json
import re
from typing import Optional
from pydantic import BaseModel, Field, ValidationError
from loguru import logger
from backend.config import settings
from .model_client import model_client
from .prompt_manager import PromptManager




ALLOWED_TAGS = {"h2", "h3", "p", "strong", "em", "blockquote", "ul", "ol", "li", "br", "img", "a", "span"}


def sanitize_content_html(html):
    """Strip inline styles and unsupported tags from article HTML."""
    if not html:
        return html
    html = re.sub(r'\s*style\s*=\s*"[^"]*"', '', html)
    html = re.sub(r"\s*style\s*=\s*'[^']*'", '', html)
    html = re.sub(r'\s*class\s*=\s*"[^"]*"', '', html)
    html = re.sub(r"\s*class\s*=\s*'[^']*'", '', html)
    html = re.sub(r'\s*id\s*=\s*"[^"]*"', '', html)
    html = re.sub(r"\s*id\s*=\s*'[^']*'", '', html)
    for tag in ["section", "div", "article", "header", "footer", "main", "aside", "nav"]:
        html = re.sub(rf'</?{tag}[^>]*>', '', html, flags=re.IGNORECASE)
    def _clean_tag(m):
        if m.group(1).lower() in ALLOWED_TAGS:
            return m.group(0)
        return m.group(2) or ''
    html = re.sub(r'<(\w+)(?:\s[^>]*)?>(.*?)</\1>', _clean_tag, html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<(?!\/?(?:h2|h3|p|strong|em|blockquote|ul|ol|li|br|img|a|span)\b)\w+[^>]*\/>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

class ArticleOutput(BaseModel):
    """Pydantic schema for AI article output validation"""
    title: str = Field(default="AI Article", min_length=1, max_length=200)
    summary: str = Field(default="", max_length=500)
    content_html: str = Field(default="", min_length=1)
    seo_keywords: str = Field(default="")


class ArticleGenerator:
    """AI article generator with robust JSON parsing."""

    def __init__(self):
        self.client = model_client
        self.prompts = PromptManager()

    def generate(self, topic: str, style: str = "marketing", length: str = "medium") -> dict:
        """Generate article from topic.

        Returns:
            {title, summary, content_html, seo_keywords, style}
        """
        logger.info("Generating | topic={}", topic)
        sp = self.prompts.get_system_prompt()
        up = self.prompts.build_user_prompt(style, topic, length)

        try:
            from backend.services.content_formatter import get_prompt_instructions
            up += "\n\n" + get_prompt_instructions()
        except ImportError:
            logger.debug("content_formatter not available for prompt enrichment")

        try:
            raw = self.client.chat(sp, up)
        except RuntimeError as e:
            logger.error("AI API call failed: {}", e)
            raise

        art = self._parse(raw)
        art["style"] = style
        art["content_html"] = sanitize_content_html(art.get("content_html", ""))
        logger.success("Done | title={}", art.get("title", "")[:40])
        return art

    def get_available_styles(self) -> list[str]:
        return self.prompts.get_available_styles()

    def _parse(self, raw: str) -> dict:
        """Robust JSON parsing with Pydantic validation.

        Strategy: JSON mode first → regex extraction → manual fallback
        """
        if not raw or not raw.strip():
            logger.error("Empty AI response")
            return self._empty_result("AI returned empty response")

        # Step 1: Extract JSON from code blocks
        json_str = self._extract_json_str(raw)

        # Step 2: Try direct JSON parse
        try:
            data = json.loads(json_str)
            validated = ArticleOutput(**data)
            logger.info("JSON parsed successfully (direct)")
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Direct JSON parse failed: {}", str(e)[:100])

        # Step 3: Try fixing common JSON issues
        try:
            fixed = self._repair_json(json_str)
            data = json.loads(fixed)
            validated = ArticleOutput(**data)
            logger.info("JSON parsed successfully (repaired)")
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Repaired JSON parse failed: {}", str(e)[:100])

        # Step 4: Manual regex fallback as last resort
        logger.warning("Falling back to manual regex extraction")
        return self._manual_fallback(raw)

    def _extract_json_str(self, raw: str) -> str:
        """Extract JSON string from AI response (may be wrapped in markdown)."""
        # Try code block
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            return m.group(1).strip()
        # Find JSON object bounds
        s = raw.find("{")
        e = raw.rfind("}")
        if s >= 0 and e > s:
            return raw[s:e + 1]
        return raw

    def _repair_json(self, text: str) -> str:
        """Fix common JSON formatting issues."""
        # Remove trailing commas
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)
        # Fix unescaped newlines in string values
        text = re.sub(r'(?<!\\)"([^"]*?)\n([^"]*?)"', r'"\1\\n\2"', text)
        return text

    def _manual_fallback(self, raw: str) -> dict:
        """Regex-based extraction as absolute last resort."""
        d = {}
        for field in ["title", "summary", "seo_keywords"]:
            m = re.search(r'"' + field + r'"\s*:\s*"(.+?)"', raw)
            if m:
                d[field] = m.group(1)

        # Try to extract content_html (handle escaped quotes)
        content_matches = re.findall(
            r'"content_html"\s*:\s*"(.*?)"\s*[,}]', raw, re.DOTALL
        )
        if content_matches:
            c = content_matches[-1]  # take last match (most complete)
            c = c.replace("\\n", "\n").replace('\\"', '"').replace("\\t", "\t")
            d["content_html"] = c

        # Fallback: use truncated raw text as content
        if not d.get("content_html"):
            d["content_html"] = raw[:2000]

        d["content_html"] = sanitize_content_html(d.get("content_html", ""))
        d.setdefault("title", "AI Article")
        d.setdefault("summary", "")
        d.setdefault("seo_keywords", "")

        logger.warning("Manual fallback used | fields_found={}", list(d.keys()))
        return d

    @staticmethod
    def _empty_result(reason: str = "") -> dict:
        """Return a safe empty result."""
        return {
            "title": "AI Article",
            "summary": "",
            "content_html": f"<p>生成失败: {reason}</p>",
            "seo_keywords": "",
        }


article_generator = ArticleGenerator()
