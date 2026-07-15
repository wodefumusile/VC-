"""AI 选题分析 Agent — 基于来源内容生成选题方案"""

import json
import re
from loguru import logger
from backend.services.ai.model_client import model_client
from backend.config import settings

ANALYSIS_PROMPT = """你是一个自媒体选题专家。根据以下参考内容，帮我分析可以写什么公众号文章。

## 参考内容

### 公众号文章：
标题：{wechat_title}
作者：{wechat_author}
摘要：{wechat_summary}
关键词：{wechat_keywords}

### 抖音视频：
标题：{douyin_title}
描述：{douyin_description}
标签：{douyin_tags}

## 任务
1. 提炼核心主题（如果参考内容太少，根据标题和标签合理推测）
2. 分析用户痛点
3. 给出3个公众号选题角度和标题

## 输出JSON：
{{
  "core_topic": "核心主题",
  "user_pain_points": ["痛点"],
  "content_angles": [
    {{"angle": "角度", "title": "标题", "target_audience": "受众"}}
  ],
  "recommended_titles": ["标题1", "标题2", "标题3"]
}}
"""


def analyze_topic(wechat_data: dict | None = None, douyin_data: dict | None = None) -> dict:
    """分析来源内容，生成选题建议"""
    if not settings.AI_API_KEY:
        return {"error": "AI API Key 未配置", "core_topic": "", "recommended_titles": []}

    wd = wechat_data or {}
    dd = douyin_data or {}

    # 如果是需要登录的抖音视频，不做AI分析，直接返回提示
    if dd.get("error") == "needs_login":
        return {
            "core_topic": "请手动输入主题",
            "user_pain_points": [],
            "content_angles": [],
            "recommended_titles": [],
            "note": "该抖音视频需登录才能获取内容。请切换到\"输入主题\"模式，手动输入你想写的主题。"
        }

    prompt = ANALYSIS_PROMPT.format(
        wechat_title=wd.get("title", "无"),
        wechat_author=wd.get("author", "无"),
        wechat_summary=(wd.get("summary") or wd.get("content", ""))[:500],
        wechat_keywords=", ".join((wd.get("keywords") or [])),
        douyin_title=dd.get("title", "无"),
        douyin_description=(dd.get("description") or "")[:300],
        douyin_tags=", ".join((dd.get("hot_tags") or [])),
    )

    try:
        content = model_client.chat(
            system_prompt="你是一个自媒体选题专家。即使参考内容很少，也根据已有信息合理推测和创作。",
            user_prompt=prompt,
            temperature=0.8,
        )

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            logger.success("选题分析完成 | 核心主题={}", result.get("core_topic", "")[:30])
            return result
        else:
            return {"raw_analysis": content, "core_topic": "分析完成", "recommended_titles": []}

    except Exception as e:
        logger.error("选题分析失败: {}", e)
        return {"error": str(e), "core_topic": "", "recommended_titles": []}


def generate_article_from_analysis(analysis: dict, style: str = "marketing", length: str = "medium") -> dict:
    """基于选题分析结果生成文章"""
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if analysis.get("note"):
        return {"error": analysis["note"]}

    topic = analysis.get("core_topic", "")
    if not topic and analysis.get("recommended_titles"):
        topic = analysis["recommended_titles"][0]
    if not topic and analysis.get("content_angles"):
        topic = analysis["content_angles"][0].get("title", "")

    if not topic:
        return {"error": "无法从分析结果中提取主题，请手动输入"}

    from backend.services.ai import article_generator
    return article_generator.generate(topic=topic, style=style, length=length)
