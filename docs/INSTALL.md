# Installation Guide

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Docker Desktop (for n8n)
- WeChat Official Account (for publishing)

## Step 1: Clone / Download Project

```bash
cd ~/Desktop
# Project is at: 公众号发文项目/
```

## Step 2: Python Environment

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Install Playwright + Chromium

```bash
# Install Playwright browsers
playwright install chromium

# Verify installation
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

## Step 5: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your values
# Required: AI_API_KEY (DeepSeek/OpenAI API key)
```

### .env Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_API_KEY` | Yes | - | DeepSeek/OpenAI API key |
| `AI_BASE_URL` | No | `https://api.deepseek.com` | API base URL |
| `AI_MODEL` | No | `deepseek-chat` | Model name |
| `SERVER_HOST` | No | `0.0.0.0` | FastAPI host |
| `SERVER_PORT` | No | `8000` | FastAPI port |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Step 6: First-Time WeChat Login

```bash
# Run a test publish to trigger login
python tests/test_single_draft.py
```

A browser window opens. Scan the QR code with WeChat.
The session is saved and reused automatically.

## Step 7: Start FastAPI

```bash
python backend/main.py
# Service runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Step 8: Install n8n (Docker)

```bash
docker run -d   --name n8n   --restart unless-stopped   -p 5678:5678   -v n8n_data:/home/node/.n8n   docker.n8n.io/n8nio/n8n
```

Open http://localhost:5678, create account, import workflow from `workflows/wechat_article_auto_publish.json`.

## Verify Installation

```bash
# Test FastAPI health
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0"}

# Test article generation
curl -X POST http://localhost:8000/api/article/generate   -H "Content-Type: application/json"   -d '{"topic":"test","style":"marketing","length":"short"}'

# Run full test suite
python tests/test_content_optimizer.py
python tests/test_n8n_workflow.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `playwright` not found | Run `playwright install chromium` |
| `openai.AuthenticationError` | Set `AI_API_KEY` in `.env` |
| Browser doesn't open | Ensure DISPLAY is set (Linux) or run on desktop |
| WeChat login expired | Re-run `python tests/test_single_draft.py` |
| n8n can't reach FastAPI | Use `host.docker.internal` instead of `localhost` |
