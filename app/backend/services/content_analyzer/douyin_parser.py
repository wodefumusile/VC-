"""抖音视频解析器 — yt-dlp(优先) + Playwright + 静态三方案
解决抖音反爬：1) yt-dlp+cookie 2) 浏览器渲染 3) HTTP静态
失败时返回友好提示，不会崩"""
import re, os, threading, json as _json
from dataclasses import dataclass, field
from loguru import logger

FOOTER_KW = ["ICP", "举报", "feedback", "违法", "不良信息", "记录美好生活", "douyin.com", "抖音-", "京公网安备"]

@dataclass
class DouyinVideo:
    title: str = ""; description: str = ""; publish_time: str = ""
    like_count: str = ""; comment_count: str = ""
    hot_tags: list = field(default_factory=list)
    engagement: dict = field(default_factory=dict)
    author: str = ""; duration: str = ""
    def to_dict(self): return {k: v for k,v in self.__dict__.items() if not k.startswith("_")}

def _ok(title): return title and not any(k in title for k in FOOTER_KW)

def _find_cookie(): 
    for p in ["cookies.txt", os.path.expanduser("~/douyin_cookies.txt")]:
        if os.path.exists(p): return p
    return None

def _extract_json_title(html):
    for p in [r'"desc"\s*:\s*"(.+?)"', r'"title"\s*:\s*"(.+?)"',
              r'__RENDER_DATA__\s*=\s*(\{.+?\});']:
        m = re.search(p, html, re.DOTALL)
        if m:
            g = m.group(1)
            if g.startswith("{"):
                try: 
                    d = _json.loads(g)
                    t = d.get("desc") or d.get("title") or ""
                    if _ok(t): return t
                except: pass
            elif len(g) > 2 and _ok(g): return g
    return ""

def _ytdlp(url, timeout=18):
    import yt_dlp
    opts = {"quiet": True, "extract_flat": False, "skip_download": True,
            "socket_timeout": timeout, "geo_bypass": True}
    c = _find_cookie()
    if c: opts["cookiefile"] = c; logger.info("cookie: {}", c)
    try:
        with yt_dlp.YoutubeDL(opts) as y:
            i = y.extract_info(url, download=False)
            v = DouyinVideo()
            v.title = i.get("fulltitle") or i.get("title") or ""
            v.description = (i.get("description") or "")[:800]
            v.author = i.get("uploader") or ""
            v.hot_tags = (i.get("tags") or [])[:10]
            v.engagement = {"view_count": str(i.get("view_count","")),
                           "like_count": str(i.get("like_count","")),
                           "comment_count": str(i.get("comment_count","")),
                           "video_id": i.get("id","")}
            return v if _ok(v.title) else None
    except Exception as e:
        if "cookies" in str(e).lower(): logger.info("yt-dlp 需cookie")
        else: logger.error("yt-dlp: {}", str(e)[:80])
    return None

def _browser(url, timeout=25):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            ctx = b.new_context(viewport={"width":1280,"height":800}, locale="zh-CN",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            pg = ctx.new_page()
            pg.goto(url, wait_until="domcontentloaded", timeout=timeout*1000)
            pg.wait_for_timeout(3000)
            html = pg.content(); body = pg.inner_text("body")
            v = DouyinVideo()
            # JSON embedded data (best source)
            jt = _extract_json_title(html)
            if jt: v.title = jt
            # meta tags
            for s in ['meta[property="og:title"]', 'meta[name="title"]']:
                el = pg.query_selector(s)
                if el and _ok(el.get_attribute("content") or ""):
                    v.title = v.title or el.get_attribute("content")
            if not v.title: v.title = pg.title()
            # description
            for s in ['meta[property="og:description"]', 'meta[name="description"]']:
                el = pg.query_selector(s)
                if el: v.description = (el.get_attribute("content") or "")[:500]
            # hashtags
            v.hot_tags = list(set(re.findall(r'#([\u4e00-\u9fa5\w]+)', body)))[:10]
            b.close()
            return v if _ok(v.title) else None
    except Exception as e: logger.error("browser: {}", str(e)[:80])
    return None

def _static(url):
    try:
        import requests; from bs4 import BeautifulSoup
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=12)
        r.encoding='utf-8'
        jt = _extract_json_title(r.text)
        if jt: return {"title":jt,"description":"","hot_tags":[],"engagement":{}}
        s = BeautifulSoup(r.text,'html.parser')
        t = ""; d = ""
        for m in s.find_all("meta"):
            if m.get("property")=="og:title": t=m.get("content","")
            if m.get("property")=="og:description": d=m.get("content","")
        t = t or (s.title.get_text(strip=True) if s.title else "")
        return {"title":t,"description":d,"hot_tags":[],"engagement":{}} if _ok(t) else None
    except Exception as e: logger.error("static: {}", e)
    return None

def auto_parse_douyin(url: str) -> dict:
    logger.info("抖音: {}", url[:60])
    for name, fn, to in [("yt-dlp",_ytdlp,22),("浏览器",_browser,28),("静态",_static,12)]:
        r = [None]
        t = threading.Thread(target=lambda: r.__setitem__(0, fn(url)), daemon=True)
        t.start(); t.join(timeout=to)
        if r[0]:
            if isinstance(r[0], DouyinVideo):
                if _ok(r[0].title):
                    logger.success("{}: {}", name, r[0].title[:30])
                    return r[0].to_dict()
            elif isinstance(r[0], dict) and _ok(r[0].get("title","")):
                logger.success("{}: {}", name, r[0]["title"][:30])
                return r[0]
    logger.warning("所有方案均无法获取视频内容")
    return {"title":"","description":"⚠️ 该视频需登录抖音才能查看。你可以在项目根目录放置 cookies.txt 文件（浏览器导出Netscape格式）来解锁，或直接切换到【输入主题】模式手动输入。","hot_tags":[],"error":"needs_login"}


