# tech-news-wecom

每天北京时间 07:00 抓取科技 RSS 新闻，调用 OpenAI 生成中文科技早报，并推送到企业微信机器人。

## 快速开始

1) 安装依赖

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) 配置 secrets

在项目根目录创建 `secrets.json`：

```json
{
  "openai_api_key": "YOUR_KEY",
  "wecom_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
}
```

说明：
- `wecom_wenhook`（拼写）也会被兼容识别为 webhook。
- 也支持环境变量 `LLM_API_KEY`（或 `OPENAI_API_KEY` / `DEEPSEEK_API_KEY`）、`WECOM_WEBHOOK`。
- 使用 DeepSeek 时：在 `secrets.json` 里用 `deepseek_api_key`（或环境变量 `DEEPSEEK_API_KEY`），并建议设置 `LLM_BASE_URL`（或 `deepseek_base_url`）为 DeepSeek 的 OpenAI 兼容地址，同时把 `LLM_MODEL`（或 `deepseek_model`）设为例如 `deepseek-chat`。

3) 运行一次（立即抓取 + 推送）

```bash
python -m tech_news_wecom.cli run-once
```

4) 常驻定时（北京时间每天 07:00）

```bash
python -m tech_news_wecom.cli schedule
```

## GitHub Actions 自动运行（推荐）

可以部署到 GitHub，通过 Actions 定时每天自动运行并推送到企业微信。

1) 把仓库推到 GitHub

2) 在 GitHub 仓库 Settings → Secrets and variables → Actions → New repository secret 添加：
- `OPENAI_API_KEY`（或改用 `LLM_API_KEY` / `DEEPSEEK_API_KEY`）
- `WECOM_WEBHOOK`
- （可选）`OPENAI_MODEL`/`LLM_MODEL`/`DEEPSEEK_MODEL`（DeepSeek 常用 `deepseek-chat`；OpenAI 默认 `gpt-4.1-mini`）
- （可选）`LLM_BASE_URL`（或 `OPENAI_BASE_URL` / `DEEPSEEK_BASE_URL`）
- （可选）`MAX_ITEMS`，默认 `20`

3) Actions 工作流文件在 `/.github/workflows/daily-briefing.yml`

说明：
- GitHub Actions 的 cron 用 UTC；已配置为每天 `23:00 UTC` 触发（即北京时间次日 `07:00`）。
- 为避免重复推送，工作流使用 Actions Cache 持久化 `data/seen.sqlite3`（尽力而为，缓存偶尔可能失效）。

## RSS 源

默认 RSS 列表在 `feeds.txt`，一行一个 URL，可自行增删。
