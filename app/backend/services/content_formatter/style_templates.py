"""Style templates - 4 preset styles for WeChat formatting"""

TEMPLATES = {
    "business": {
        "name": "商务专业风",
        "h1_color": "#1a3c6e", "h2_color": "#2c5aa0",
        "body_color": "#333333", "body_size": "15px", "line_height": "1.9",
    },
    "knowledge": {
        "name": "知识科普风",
        "h1_color": "#2c3e50", "h2_color": "#34495e",
        "body_color": "#444444", "body_size": "16px", "line_height": "2.0",
    },
    "marketing": {
        "name": "营销转化风",
        "h1_color": "#e74c3c", "h2_color": "#c0392b",
        "body_color": "#333333", "body_size": "16px", "line_height": "1.9",
    },
    "personal": {
        "name": "个人IP风",
        "h1_color": "#6c5ce7", "h2_color": "#a29bfe",
        "body_color": "#555555", "body_size": "16px", "line_height": "2.0",
    },
}

PROMPT_INSTRUCTIONS = """
## 输出格式要求（非常重要！）
你必须输出包含HTML标签的公众号文章，结构如下：
- 正文第1段：用<p>标签，一句话点明核心观点
- 每个小节用<h2>小标题</h2>分隔
- 每个小节下2-3段，每段用<p>标签
- 数字和数据用<strong>加粗</strong>
- 案例或数据引用用<blockquote>包裹
- 严禁在正文中出现（正文）（解释）（标题）等标签文字！
- 不要用markdown格式（##, **等），直接用HTML标签
"""


def get_template(name: str) -> dict:
    return TEMPLATES.get(name, TEMPLATES["knowledge"])


def get_all_templates() -> list:
    return [{"id": k, "name": v["name"]} for k, v in TEMPLATES.items()]


def get_prompt_instructions() -> str:
    return PROMPT_INSTRUCTIONS