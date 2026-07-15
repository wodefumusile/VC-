"""Image Planner Agent — analyzes article content, plans cover + illustration images.

Phase 17 v2.0: Input article → output image generation plan.
"""

import json
import re
from loguru import logger
from backend.services.ai.model_client import model_client


PLANNER_PROMPT = """你是一个公众号文章配图规划专家。分析以下文章，规划配图方案。

## 文章信息
标题：{title}
分类：{category}

## 文章内容
{content}

## 任务
分析文章内容，规划配图方案：

1. **封面图**: 设计一张吸引点击的封面图 prompt（中文描述，风格现代）
2. **正文插图**: 根据文章段落决定需要几张插图（建议 2-4 张），每张给出 prompt 和位置

## 规则
- 封面图 prompt 要突出标题核心卖点，适合公众号卡片展示（16:9 比例感）
- 插图 prompt 要贴合对应段落内容，风格统一
- 技术/科技类文章用简洁商务风格
- 个人成长类用温暖人文风格

## 输出 JSON（只输出 JSON，不要 markdown）:
{{
  "cover": {{
    "prompt": "封面图中文描述 prompt"
  }},
  "images": [
    {{"position": 1, "prompt": "第1张插图描述", "reason": "配图原因"}},
    {{"position": 2, "prompt": "第2张插图描述", "reason": "配图原因"}}
  ]
}}
"""


class ImagePlanner:
    """AI-powered image planning agent.

    Analyzes article content and outputs a structured image
    generation plan with cover + body illustrations.
    """

    def __init__(self):
        self.client = model_client

    def plan(self, title: str, content: str, category: str = "general") -> dict:
        """Analyze article and generate image plan.

        Args:
            title: Article title
            content: Article body text (plain or HTML, we strip tags)
            category: Content category for style guidance

        Returns:
            {"cover": {"prompt": "..."}, "images": [...]}
        """
        # Strip HTML tags for analysis
        plain_text = re.sub(r"<[^>]+>", "", content)
        # Truncate to avoid token overflow
        truncated = plain_text[:3000]

        prompt = PLANNER_PROMPT.format(
            title=title,
            category=category,
            content=truncated,
        )

        logger.info("ImagePlanner analyzing | title={} | content_len={}",
                     title[:30], len(plain_text))

        try:
            raw = self.client.chat(
                system_prompt="你是一个公众号配图规划专家。只输出 JSON，不要有任何其他文字。",
                user_prompt=prompt,
                temperature=0.7,
            )

            # Parse JSON from response
            data = self._parse(raw)

            cover_count = 1 if data.get("cover", {}).get("prompt") else 0
            img_count = len(data.get("images", []))
            logger.success("ImagePlanner done | cover={} illustrations={}",
                           cover_count, img_count)
            return data

        except Exception as e:
            logger.error("ImagePlanner failed: {}", e)
            return {"cover": {}, "images": []}

    def _parse(self, raw: str) -> dict:
        """Extract JSON from AI response."""
        # Try code block
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
        # Find JSON object
        s = raw.find("{")
        e = raw.rfind("}")
        if s >= 0 and e > s:
            raw = raw[s:e + 1]
        # Fix common JSON issues
        raw = re.sub(r",\s*}", "}", raw)
        raw = re.sub(r",\s*]", "]", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed, returning empty plan")
            return {"cover": {}, "images": []}


image_planner = ImagePlanner()
