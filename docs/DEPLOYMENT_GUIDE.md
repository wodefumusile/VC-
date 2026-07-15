# 公众号AI运营系统 — 部署指南 v2.1.3

## 1. 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| OS | Windows 10+ / macOS 12+ / Linux |
| 内存 | 2GB+ |
| 浏览器 | Chrome/Edge (Playwright auto-downloads Chromium) |

## 2. 安装

```bash
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
# Edit .env: set AI_API_KEY and ADMIN_TOKEN
python -m backend.main
```

Open http://localhost:8000

## 3. 启动模式

| 模式 | APP_ENV | 特性 |
|------|---------|------|
| dev | development | auto-reload, full errors |
| prod | production | no Swagger, no tracebacks, file logging |

## 4. 常见问题

| 问题 | 解决 |
|------|------|
| AI generate 502 | Check DeepSeek key has sk- prefix |
| WeChat publish fail | First login needs QR scan, session cached |
| Config not applied | Restart after .env changes |
| Obsidian slow | First scan caches, subsequent incremental |

## 5. 目录

```
├── backend/          # App code
├── storage/          # SQLite + cache
├── logs/             # Logs (error kept 30 days)
├── backup/           # Daily auto-backup
├── knowledge/        # Obsidian file pool
├── docs/             # Documentation
├── .env              # Env vars (sensitive!)
└── .env.example      # Config template
```
