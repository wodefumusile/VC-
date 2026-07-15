from __future__ import annotations
"""微信公众号 页面定位策略 v2.5

新增：作者输入框定位
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore


class EditorSelectors:
    """微信公众号图文编辑器定位策略"""

    def __init__(self, page: Page):
        self.page = page

    # === 标题输入 ===

    def find_title_input(self):
        """定位标题输入框 — 优先 placeholder/text 语义定位"""
        strategies = [
            lambda: self.page.get_by_placeholder("请输入标题"),
            lambda: self.page.locator('[placeholder*="标题"]'),
            lambda: self.page.locator("#title:visible"),
            lambda: self.page.locator('[id*="title"]:visible').first,
        ]
        for fn in strategies:
            try:
                el = fn()
                if el and el.count() > 0:
                    return el.first
            except Exception:
                pass
        return None

    # === 作者输入 ===

    def find_author_input(self):
        """定位作者输入框 — 微信编辑器作者栏"""
        strategies = [
            lambda: self.page.get_by_placeholder("请输入作者"),
            lambda: self.page.locator('[placeholder*="作者"]'),
            lambda: self.page.locator("#author:visible"),
            lambda: self.page.locator('[id*="author"]:visible').first,
        ]
        for fn in strategies:
            try:
                el = fn()
                if el and el.count() > 0:
                    return el.first
            except Exception:
                pass

        # fallback: 查找"作者"标签旁边的 input
        try:
            author_label = self.page.get_by_text("作者", exact=True)
            if author_label.count() > 0:
                # 尝试找同行的 input
                parent = author_label.first.locator("xpath=..")
                inp = parent.locator("input:visible")
                if inp.count() > 0:
                    return inp.first
        except Exception:
            pass
        return None

    # === 正文编辑区 ===

    def find_content_editor(self):
        """定位正文编辑区 - 遍历所有contenteditable元素"""
        try:
            editable = self.page.locator('[contenteditable="true"]:visible')
            if editable.count() > 0:
                return editable.first

            bodies = self.page.locator("body")
            for i in range(bodies.count()):
                body = bodies.nth(i)
                if body.get_attribute("contenteditable") == "true":
                    return body

            return None
        except Exception:
            return None

    def inject_content_html(self, html: str) -> bool:
        """通过JS注入HTML到编辑器 — 三层fallback"""
        # 对HTML做JS字符串安全转义
        safe_html = html.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        code = f"""
        (() => {{
            let ed = document.querySelector('[contenteditable="true"]');
            if (ed) {{ ed.innerHTML = `{safe_html}`; ed.dispatchEvent(new Event('input', {{bubbles: true}})); return 'contenteditable'; }}

            let editor = document.getElementById('ueditor_0') ||
                         document.querySelector('.edui-editor-iframeholder') ||
                         document.querySelector('.editor_iframe');
            if (editor) {{
                let body = editor.contentDocument ? editor.contentDocument.body : editor;
                body.innerHTML = `{safe_html}`;
                return 'editor_frame';
            }}

            let areas = document.querySelectorAll('[role="textbox"], .ql-editor, .edit_area, #ueditor_textarea');
            if (areas.length > 0) {{
                areas[0].innerHTML = `{safe_html}`;
                return 'textbox_role';
            }}

            return null;
        }})();
        """
        try:
            result = self.page.evaluate(code)
            if result:
                return True
        except Exception:
            pass
        return False

    # === 摘要输入 ===

    def find_summary_input(self):
        """定位摘要输入框 - 多种fallback"""
        strategies = [
            lambda: self.page.get_by_placeholder("请输入摘要"),
            lambda: self.page.get_by_placeholder("填写摘要"),
            lambda: self.page.locator('[placeholder*="摘要"]'),
            lambda: self.page.locator("textarea:visible").first,
            lambda: self.page.locator("input[name*='summary']"),
            lambda: self.page.locator("input[name*='abstract']"),
        ]
        for fn in strategies:
            try:
                el = fn()
                if el and el.count() > 0:
                    return el.first
            except Exception:
                pass
        return None

    def click_summary_area(self) -> bool:
        """点击摘要相关区域以触发输入框显示"""
        click_texts = ["摘要", "填写摘要", "文章摘要"]
        for text in click_texts:
            try:
                el = self.page.get_by_text(text, exact=False)
                if el.count() > 0:
                    el.first.click()
                    self.page.wait_for_timeout(1000)
                    return True
            except Exception:
                pass
        return False

    # === 保存按钮 ===

    def find_save_button(self):
        """定位保存/存草稿按钮"""
        save_texts = ["保存", "存草稿", "保存草稿", "发布", "群发"]
        for text in save_texts:
            try:
                el = self.page.get_by_text(text, exact=True)
                if el.count() > 0:
                    return el.first
            except Exception:
                pass

        try:
            buttons = self.page.locator("button:visible")
            for i in range(buttons.count()):
                btn_text = (buttons.nth(i).inner_text() or "").strip()
                if any(w in btn_text for w in ["保存", "存草稿", "草稿"]):
                    return buttons.nth(i)
        except Exception:
            pass

        return None

    # === 封面图片 ===

    def find_cover_upload(self):
        """定位封面图片上传区域"""
        try:
            el = self.page.get_by_text("封面", exact=False)
            if el.count() > 0:
                return el.first
        except Exception:
            pass
        return None