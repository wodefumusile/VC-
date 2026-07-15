"""
SEO Optimizer

Uses existing ModelClient for title and content SEO optimization.
"""

import json
import re
from loguru import logger
from backend.services.ai.model_client import model_client
from backend.services.ai.prompt_manager import PromptManager


class SEOOptimizer:
    """Article SEO optimizer using AI + rules"""

    def __init__(self):
        self.client = model_client
        self.prompts = PromptManager()

    def optimize(self, title: str, content_html: str, seo_keywords: str = "") -> dict:
        """SEO optimize an article

        Returns:
            {optimized_title, seo_description, keywords, score, suggestions}
        """
        logger.info("SEO optimize | title_len={} | kw={}", len(title), seo_keywords[:50])

        base_score, rule_suggestions = self._rule_check(title, content_html, seo_keywords)
        ai_result = self._ai_analyze(title, content_html, seo_keywords)

        optimized_title = ai_result.get("optimized_title", title)
        seo_description = ai_result.get("seo_description", self._extract_description(content_html))
        keywords = ai_result.get("keywords", [k.strip() for k in seo_keywords.split(",") if k.strip()])
        score = max(base_score, ai_result.get("score", base_score))
        suggestions = rule_suggestions + ai_result.get("suggestions", [])

        return {
            "optimized_title": optimized_title,
            "seo_description": seo_description,
            "keywords": keywords,
            "score": score,
            "suggestions": suggestions,
        }

    def _rule_check(self, title: str, content_html: str, keywords: str) -> tuple:
        """Fast rule-based SEO checks (no API call)"""
        score = 70
        suggestions = []

        title_len = len(title)
        if title_len < 10:
            suggestions.append("Title too short (<10 chars)")
            score -= 10
        elif title_len > 40:
            suggestions.append("Title too long (>40 chars)")
            score -= 5

        kw_list = [k.strip() for k in keywords.split(",") if k.strip()]
        if not kw_list:
            suggestions.append("No SEO keywords found")
            score -= 10
        elif not any(kw.lower() in title.lower() for kw in kw_list):
            suggestions.append("Title lacks any SEO keyword")
            score -= 10

        text = re.sub(r"<[^>]+>", "", content_html)
        if len(text) < 300:
            suggestions.append("Content too short (<300 chars)")
            score -= 15
        elif len(text) < 500:
            suggestions.append("Content somewhat short (<500 chars)")
            score -= 5

        h2_count = len(re.findall(r"<h2", content_html, re.I))
        if h2_count == 0:
            suggestions.append("No H2 subheadings found")
            score -= 10

        return max(score, 0), suggestions

    def _ai_analyze(self, title: str, content_html: str, keywords: str) -> dict:
        """AI-enhanced SEO analysis"""
        text_content = re.sub(r"<[^>]+>", "", content_html)[:2000]
        user_prompt = f"Title: {title}\nKeywords: {keywords}\nContent (first 2000 chars): {text_content}"

        try:
            system_prompt = self._load_seo_system_prompt()
            raw = self.client.chat(system_prompt, user_prompt, temperature=0.3)
            return self._parse_json(raw)
        except Exception as e:
            logger.warning("AI SEO analysis failed, falling back to rules: {}", e)
            return {}

    def _load_seo_system_prompt(self) -> str:
        try:
            return self.prompts.load_prompt("seo")
        except (FileNotFoundError, ValueError):
            return """You are a Chinese SEO expert. Analyze the article and output JSON:
{
  "optimized_title": "optimized title (15-30 Chinese chars)",
  "seo_description": "SEO description (80-120 chars)",
  "keywords": ["kw1", "kw2", "kw3"],
  "score": 85,
  "suggestions": ["tip1", "tip2"]
}
Output ONLY valid JSON."""

    def _parse_json(self, raw: str) -> dict:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        return {}

    def _extract_description(self, html: str) -> str:
        text = re.sub(r"<[^>]+>", "", html).strip()
        return text[:100]


seo_optimizer = SEOOptimizer()
