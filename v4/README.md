# 公众号AI运营系统 V4

> 基于 n8n + DeepSeek + PostgreSQL 的生产级公众号自动运营工作流

---

## 架构

```
用户输入/定时触发
    ↓
② 知识检索 (PostgreSQL) ← 品牌库/Prompt/禁用词
    ↓
④ 行业分析 Agent ──→ DeepSeek
⑤ 用户分析 Agent ──→ DeepSeek
⑥ 内容规划 Agent ──→ DeepSeek
⑦ 写作 Agent     ──→ DeepSeek
⑧ SEO优化 Agent  ──→ DeepSeek
⑨ 内容审核 Agent ──→ DeepSeek
    ↓
⑩ 平台违规检测 (wordscheck)
    ↓
⑪ MD → 公众号 HTML
    ↓
⑫ 微信草稿 API ──→ 服务号草稿箱
    ↓
⑬ 人工审核 ←→ Webhook 回调 / ⑭ 自动发布
    ↓
通知推送
```

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 2. 启动服务
docker-compose -f docker-compose.v4.yml up -d

# 3. 导入工作流
docker exec n8n-v4 n8n import:workflow \
  --input=/knowledge/公众号AI运营-V4.json \
  --projectId=<你的项目ID>

# 4. 配置 n8n 凭据
# - DeepSeek Header Auth: Bearer sk-xxx
# - WeChat Official Account: appid + appsecret

# 5. 初始化品牌知识库
docker exec -i n8n-v4-postgres psql -U n8n -d n8n_wechat < init.sql
```

## 服务

| 服务 | 端口 | 说明 |
|------|------|------|
| n8n | 5678 | 工作流引擎 |
| PostgreSQL | 5432 | 品牌库 + 日志 |
| wordscheck | 8080 | 敏感词检测 |
| bridge | 9999 | 微信API桥接（容器内） |

## 数据库表

| 表 | 用途 |
|----|------|
| brand_knowledge | 品牌信息/产品/禁用词 |
| articles | 文章记录 |
| publish_logs | 发布日志 |
| workflow_logs | 执行日志 |
| prompts | Agent Prompt 配置 |

## API

```bash
# 生成文章（手动模式，存草稿）
curl -X POST http://localhost:5678/webhook/article-v4 \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI如何改变制造业","publishMode":"manual"}'

# 审核通过后发布
curl -X POST http://localhost:5678/webhook/review-approve \
  -H "Content-Type: application/json" \
  -d '{"media_id":"xxx","action":"publish"}'

# 自动模式（直接发布）
curl -X POST http://localhost:5678/webhook/article-v4 \
  -H "Content-Type: application/json" \
  -d '{"topic":"数字化转型趋势","publishMode":"auto"}'
```

## V2 升级路线

- [ ] 启用 Qdrant 向量数据库
- [ ] 接入 BGE Embedding 模型
- [ ] 知识检索节点切换到 Qdrant
- [ ] 文档自动切片 + 向量化
- [ ] PostgreSQL → Qdrant 数据同步

## 文件清单

```
v4/
├── docker-compose.v4.yml   # 服务编排
├── .env.example            # 环境变量模板
├── init.sql                # 数据库建表 + 种子数据
├── 公众号AI运营-V4.json     # n8n 工作流 (34节点)
└── README.md               # 本文件
```
