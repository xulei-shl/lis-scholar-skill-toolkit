# LIS RSS Daily Summary Skill

## 概述

这是一个 Claude Code skill，用于从 lis-rss-api 服务获取每日文章汇总。当用户请求"每日总结"、"今天的文章"等内容时，Claude 会自动使用此 skill。

## 功能特性

- 自动获取每日文章汇总
- 支持指定日期和文章数量
- JSON 和美化输出格式
- 完整的错误处理和提示
- 渐进式文档加载，节省 token
- 从 .env 文件读取配置，避免硬编码

## 使用方式

### 在 Claude Code 中

直接询问：
- "今天的文章汇总"
- "显示每日总结"
- "获取 daily summary"
- "RSS digest"

### 命令行

```bash
# 基本用法（需要先配置 .env）
python scripts/fetch-summary.py

# 指定日期
python scripts/fetch-summary.py --date 2025-02-11

# JSON 输出
python scripts/fetch-summary.py --json
```

## 前置条件

1. lis-rss-api 服务运行在 `http://10.40.92.18:8007`
2. 已配置 .env 文件中的 `LIS_RSS_USER_ID` 和 `LIS_RSS_API_KEY`
3. Python 3.7+ 和依赖库（`requests`, `python-dotenv`）

## 配置

在 skill 目录创建 `.env` 文件：

```bash
# LIS RSS API 配置
LIS_RSS_USER_ID=1
LIS_RSS_API_KEY=your-secret-key-here
LIS_RSS_BASE_URL=http://10.40.92.18:8007
```

**注意**: .env 文件包含敏感信息，应在 .gitignore 中排除。

### 安装依赖

```bash
pip install python-dotenv requests
```

## 目录结构

```
lis-rss-daily-summary/
├── SKILL.md                    # Skill 主文件
├── README.md                   # 本文件
├── .env                        # 配置文件（user_id, api_key, base_url）
├── scripts/
│   └── fetch-summary.py        # 执行脚本（读取 .env）
└── references/                 # 详细文档（按需加载）
    ├── api-specification.md     # API 规范
    ├── response-formats.md     # 响应格式
    └── troubleshooting.md       # 问题排查
```

## 参数说明

| 参数 | 简写 | 说明 | 必需 |
|------|------|------|------|
| --user-id | -u | 用户 ID | 否* |
| --api-key | -k | API 密钥 | 否* |
| --date | -d | 日期 YYYY-MM-DD | 否 |
| --limit | -l | 文章数量限制 | 否 |
| --json | | 输出纯 JSON | 否 |

* 可通过 .env 文件配置，无需每次输入

## 响应状态

| 状态 | 说明 | 退出码 |
|------|------|--------|
| success | 找到文章并生成总结 | 0 |
| empty | 当日无新文章 | 1 |
| error | API 或配置错误 | 2 |

## Token 优化

此 skill 采用以下策略节省主 agent 的上下文 token：

1. **Scripts/** - 执行但不加载到上下文
2. **References/** - 详细文档按需加载
3. **精简 SKILL.md** - 只保留核心信息
4. **.env 配置** - 避免在代码中硬编码敏感信息

预计节省 ~3900 tokens/次调用。

## 故障排除

遇到问题？查看 [完整故障排除指南](references/troubleshooting.md)。

常见问题：
- **连接失败**: 确认服务运行在 `http://10.40.92.18:8007`
- **认证失败**: 检查 .env 中的 API Key 配置
- **无新文章**: 正常行为，非错误
- **缺少依赖**: 运行 `pip install python-dotenv requests`

## 开发者

基于 lis-rss-api CLI 规范创建。
完整文档见项目 `docs/lis-rss-api-CLI.md`。
