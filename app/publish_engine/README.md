# publish-engine — Playwright 发布引擎

微信公众号个人订阅号后台浏览器自动化。

## 核心能力

- 浏览器启动（Chromium Persistent Context）
- 扫码登录 + 登录态持久化
- 登录状态检测
- 公众号后台页面访问

## 使用

```python
from publish_engine.browser.browser_manager import browser_manager
from publish_engine.auth.login import start_login
from publish_engine.auth.session import check_login
from publish_engine.pages.wechat_page import open_home

# 启动浏览器
browser_manager.start()
page = browser_manager.new_page()

# 登录（首次需扫码）
result = start_login(page)
print(result)  # {"success": True, "message": "已登录"}

# 进入后台
home = open_home(page)
print(home["url"])

# 关闭
browser_manager.close()
```

## 登录状态

登录数据保存在 `storage/user_data/`（已加入 `.gitignore`）。

- 首次运行：弹出浏览器窗口，微信扫码 → 登录态自动保存
- 后续运行：自动恢复会话，无需重新扫码

## 目录结构

```
publish-engine/
├── browser/            # 浏览器管理
│   ├── config.py       # 配置
│   └── browser_manager.py  # 管理器
├── auth/               # 认证
│   ├── login.py        # 登录流程
│   └── session.py      # 会话检测
├── pages/              # 页面操作
│   └── wechat_page.py  # 公众号后台
├── storage/user_data/  # 浏览器持久化数据
└── logs/               # 运行日志
```
