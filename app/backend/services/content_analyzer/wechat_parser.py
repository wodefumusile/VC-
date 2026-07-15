"""微信公众号文章解析器 — 通过 Playwright 抓取文章页面内容"""
import re
import asyncio
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class WechatArticle:
    title: str = ""
    author: str = ""
    publish_time: str = ""
    content: str = ""
    summary: str = ""
    keywords: list = field(default_factory=list)
    image_count: int = 0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "publish_time": self.publish_time,
            "content": self.content,
            "summary": self.summary,
            "keywords": self.keywords,
            "image_count": self.image_count,
        }


def _parse_with_playwright_sync(url: str) -> dict | None:
    """在同步函数中使用 Playwright，用于线程调用"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="networkidle", timeout=30000)

        article = WechatArticle()

        for sel in ["#activity-name", ".rich_media_title", "h1.rich_media_title"]:
            el = page.query_selector(sel)
            if el:
                article.title = el.inner_text().strip()
                break

        author_el = page.query_selector("#js_name, .rich_media_meta_nickname")
        if author_el:
            article.author = author_el.inner_text().strip()

        time_el = page.query_selector("#publish_time, .rich_media_meta_text")
        if time_el:
            article.publish_time = time_el.inner_text().strip()

        for sel in ["#js_content", ".rich_media_content"]:
            el = page.query_selector(sel)
            if el:
                article.content = el.inner_text().strip()
                break
        if not article.content:
            article.content = page.inner_text("body")

        article.summary = article.content[:200].replace("\n", " ")
        images = page.query_selector_all("#js_content img, .rich_media_content img")
        article.image_count = len(images)

        from collections import Counter
        words = re.findall(r'[\u4e00-\u9fa5]{2,4}', article.content)
        counter = Counter(words)
        article.keywords = [w for w, _ in counter.most_common(10) if len(w) >= 2]

        browser.close()
        logger.success("公众号文章解析完成 | 标题={} 字数={}", article.title[:30], len(article.content))
        return article.to_dict()


def parse_wechat_article(url: str) -> dict | None:
    """在异步上下文中安全调用 Playwright"""
    import threading
    result = [None]
    error = [None]

    def _run():
        try:
            result[0] = _parse_with_playwright_sync(url)
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout=60)

    if error[0]:
        logger.error("公众号文章解析失败: {}", error[0])
        return None
    return result[0]


def parse_wechat_static(url: str) -> dict | None:
    """静态 HTTP 解析（无需 Playwright）"""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        article = WechatArticle()
        title = soup.find(id="activity-name")
        if title: article.title = title.get_text(strip=True)
        author = soup.find(id="js_name")
        if author: article.author = author.get_text(strip=True)
        time_el = soup.find(id="publish_time")
        if time_el: article.publish_time = time_el.get_text(strip=True)

        content_div = soup.find(id="js_content")
        if content_div:
            article.content = content_div.get_text("\n", strip=True)
            article.summary = article.content[:200]
            article.image_count = len(content_div.find_all("img"))
            from collections import Counter
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', article.content)
            article.keywords = [w for w, _ in Counter(words).most_common(10) if len(w) >= 2]

        if article.title and article.content:
            logger.success("静态解析完成 | 标题={}", article.title[:30])
            return article.to_dict()
        return None
    except Exception as e:
        logger.error("静态解析失败: {}", e)
        return None


def auto_parse_wechat(url: str) -> dict | None:
    """自动选择解析方式"""
    result = parse_wechat_static(url)
    if result and result.get("title") and result.get("content"):
        return result
    logger.info("静态解析不完整，切换到 Playwright")
    return parse_wechat_article(url)
