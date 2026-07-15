# 公众号AI运营系统 — 管理员指南 v2.1.3

## 日志查看

日志文件位于 `logs/` 目录：

| 文件 | 内容 | 保留 |
|------|------|------|
| `app_YYYY-MM-DD.log` | 全量应用日志 | 7 天 |
| `error_YYYY-MM-DD.log` | 仅 ERROR 级别 | 30 天 |
| `article_generate_*.log` | 文章生成记录 | 7 天 |
| `wechat_publish_*.log` | 微信发布记录 | 7 天 |
| `workflow_*.log` | 流水线执行记录 | 7 天 |

### 查看实时日志

```bash
# Windows
Get-Content logs\app_*.log -Wait -Tail 50

# Mac/Linux
tail -f logs/app_*.log
```

## 备份恢复

### 自动备份

系统启动后每天自动备份 SQLite 数据库到 `backup/` 目录，文件名格式 `articles_YYYYMMDD.db`。

### 手动备份

```bash
copy storage\articles.db backup\articles_manual_20260715.db
```

### 恢复

```bash
copy backup\articles_20260715.db storage\articles.db
# 重启服务
```

## 故障排查

### 服务无法启动

1. 检查 Python 版本 >= 3.10
2. 检查 `.env` 是否存在（从 `.env.example` 复制）
3. 检查 `AI_API_KEY` 是否配置
4. 查看 `logs/error_*.log`

### AI 生成失败

1. 检查 DeepSeek 账户余额
2. 测试网络: `curl https://api.deepseek.com`
3. 在配置页点击「测试连接」验证 Key

### 微信发布失败

1. 确认 Chrome 已安装
2. 确认已手动扫码登录过一次
3. 检查 `logs/wechat_publish_*.log`
4. 清除缓存: 删除 `storage/user_data/`

### 配置页面 403

1. 检查 `.env` 中 `ADMIN_TOKEN` 是否配置
2. 请求需携带: `Authorization: Bearer <ADMIN_TOKEN>`

## 环境变量参考

| 变量 | 必填 | 说明 |
|------|------|------|
| `AI_API_KEY` | 是 | DeepSeek API Key |
| `ADMIN_TOKEN` | 是 | 配置页后端鉴权 |
| `IMAGE_API_KEY` | 否 | 即梦 AI Key（为空则跳过图片） |
| `OBSIDIAN_PATH` | 否 | Obsidian Vault 路径（为空则跳过知识库） |
| `APP_ENV` | 否 | development / production |
| `SERVER_PORT` | 否 | 默认 8000 |
| `LOG_LEVEL` | 否 | DEBUG / INFO / WARNING |
