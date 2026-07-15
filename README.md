# 公众号AI智能运营系统 V2.2.1

> 🚀 AI 驱动的微信公众号内容创作与自动发布系统

[![Version](https://img.shields.io/badge/version-2.2.1-blue)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.12+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

## ✨ 功能

- 🤖 **AI 写文章** — 接入 DeepSeek，输入主题即可生成专业公众号文章
- 🎨 **AI 配图** — 接入火山方舟 Seedream 4.0，自动生成文章插图
- 📤 **自动发布** — 通过 Playwright 自动化，一键保存到公众号草稿箱
- 📊 **质量检测** — 内置敏感词过滤、内容评分
- ⚙️ **Web 管理界面** — 可视化配置，无需改代码

## 📦 快速安装

### 1. 下载

`ash
# 从 releases 下载最新版本
# 或克隆仓库
git clone https://github.com/your-org/wechat-ai-publisher.git
cd wechat-ai-publisher
`

### 2. 安装

`ash
# Windows: 双击 一键安装.bat
# 或手动安装:
pip install -r app/requirements.txt
playwright install chromium
`

### 3. 配置

`ash
# 复制配置模板
copy app\.env.example app\.env

# 编辑 app\.env，填入你的 API Key:
#   AI_API_KEY=sk-xxxxxxxx    (DeepSeek，必填)
#   IMAGE_API_KEY=ark-xxxxxx  (火山方舟，可选)
`

### 4. 启动

`ash
# Windows: 双击 一键启动.bat
# 或手动启动:
cd app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
`

浏览器打开 **http://localhost:8000**

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI + Uvicorn |
| AI 引擎 | DeepSeek (OpenAI 兼容接口) |
| 图片生成 | 火山方舟 Seedream 4.0 |
| 浏览器自动化 | Playwright + Chrome CDP |
| 工作流引擎 | n8n (Docker) |
| 前端 | 原生 HTML/CSS/JS (单页应用) |

## 📁 项目结构

`
├── 一键安装.bat          # 首次安装脚本
├── 一键启动.bat          # 启动系统
├── 一键停止.bat          # 关闭系统
├── app/                  # 系统核心
│   ├── .env.example      # 配置模板
│   ├── backend/          # FastAPI 后端
│   │   ├── api/          # API 路由
│   │   ├── services/     # 业务逻辑
│   │   ├── config/       # 配置管理
│   │   └── web_ui.py     # Web 界面
│   ├── publish_engine/   # 发布引擎
│   │   ├── wechat/       # 公众号编辑器操作
│   │   ├── browser/      # 浏览器管理
│   │   └── auth/         # 登录认证
│   ├── prompts/          # AI 提示词模板
│   └── storage/          # 数据库
├── config/               # Docker 配置
├── docs/                 # 文档
└── releases/             # 打包版本
`

## 🔧 系统要求

- Windows 10/11 64位
- Python 3.12+
- Chrome 浏览器
- (可选) Docker Desktop — 用于 n8n 工作流引擎

## 📖 文档

- [安装教程](docs/客户安装教程_v2.2.1.md)
- [使用手册](docs/使用手册.md)
- [故障排查](docs/故障排查.md)

## ⚠️ 注意事项

1. DeepSeek API 需要充值使用（约 1 元/百万字）
2. 首次发布需要扫码登录公众号
3. 系统只负责保存到草稿箱，群发需要手动操作
4. 请勿将 .env 文件上传到公开仓库

## 📄 License

MIT License
