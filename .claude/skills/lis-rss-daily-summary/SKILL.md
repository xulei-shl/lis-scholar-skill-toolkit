---
name: lis-rss-daily-summary
description: 获取 lis-rss-api 每日文章汇总并保存为 markdown。当用户请求"每日总结"、"文章汇总"、"RSS digest"、"今天的文章"、"daily news"，或提及 "lis-rss"、"RSS articles"、"daily summary" 时使用。
allowed-tools: Bash, Write, Skill
user-invocable: true
---

# LIS RSS 每日汇总

## 核心工作流

### 步骤 1：并行调用脚本（按类型分离）

**⚠️ 重要优化**：使用 `--type` 参数并行生成两类独立总结

```bash
# 并行调用两个脚本（在同一条消息中执行多个 Bash）
python3 $CLAUDE_PROJECT_DIR/.claude/skills/lis-rss-daily-summary/scripts/fetch-summary.py --save --type journal
```

```bash
python3 $CLAUDE_PROJECT_DIR/.claude/skills/lis-rss-daily-summary/scripts/fetch-summary.py --save --type blog_news
```

> **路径规范**：使用 `$CLAUDE_PROJECT_DIR` 环境变量，确保跨工作目录的可靠路径解析。
>
> **并行执行**：两条命令必须在同一条响应中并行调用，以提高效率。

> **参数说明**：
> - `--type journal`: 仅生成期刊论文总结（`source_type = 'journal'`）
> - `--type blog_news`: 生成博客+新闻资讯总结（`source_type IN ('blog', 'news')`）

### 步骤 2：处理响应

**检查每个脚本返回的状态**：

| 状态 | 动作 | 文件生成 |
|------|------|----------|
| `success` | 记录文件路径，准备上传 | ✅ 已生成 |
| `empty` | 跳过（不生成 md 文件） | ❌ 不生成 |
| `error` | 查阅 [troubleshooting.md](references/troubleshooting.md) | ❌ 不生成 |

**文件命名规则**：
- 期刊总结：`daily-summary-journal-YYYY-MM-DD.md`
- 博客资讯总结：`daily-summary-blog-news-YYYY-MM-DD.md`

**示例判断逻辑**：
```python
# 统计成功/空/错误状态
success_count = sum(1 for result in results if result.status == "success")
empty_count = sum(1 for result in results if result.status == "empty")
error_count = sum(1 for result in results if result.status == "error")

# 只有 success_count > 0 时才执行后续步骤
if success_count == 0 and empty_count == 2:
    # 两个类型都为空，询问用户
    pass
elif success_count > 0:
    # 至少有一个成功，继续上传和报告
    pass
```

### 步骤 3：批量上传到 WPS 云盘

**仅上传成功生成的文件**：

```python
# 获取成功生成的文件列表（从步骤2的结果中提取）
success_files = [
    "$CLAUDE_PROJECT_DIR/outputs/rss/daily-summary-journal-YYYY-MM-DD.md",
    "$CLAUDE_PROJECT_DIR/outputs/rss/daily-summary-blog-news-YYYY-MM-DD.md"
]

# 为每个成功文件调用上传（同一条消息中并行执行）
Skill(skill="wps-file-upload", args=f"--file {file} --path CC-datas/rss --create-path")
```

**错误处理**：
- 单个文件上传失败仅记录警告，不影响其他文件
- 本地文件始终保存成功，WPS 上传失败不影响整体完成状态

### 步骤 4：汇总报告

**输出模板**：

```
✅ RSS 每日汇总生成完成

📊 统计:
- 日期: YYYY-MM-DD
- 生成报告: X 个
  - 期刊论文: N 篇 → daily-summary-journal-YYYY-MM-DD.md
  - 博客资讯: M 篇 → daily-summary-blog-news-YYYY-MM-DD.md

📁 文件路径:
- 本地: outputs/rss/daily-summary-journal-YYYY-MM-DD.md
- 本地: outputs/rss/daily-summary-blog-news-YYYY-MM-DD.md
- WPS云盘: CC-datas/rss/{文件名} (文件ID: {id}, 大小: {size} 字节)
```

**仅生成期刊时**：
```
✅ RSS 每日汇总生成完成（期刊论文）

📊 统计:
- 日期: YYYY-MM-DD
- 期刊论文: N 篇

📁 文件路径:
- 本地: outputs/rss/daily-summary-journal-YYYY-MM-DD.md
- WPS云盘: CC-datas/rss/daily-summary-journal-YYYY-MM-DD.md
```

**仅生成博客资讯时**：
```
✅ RSS 每日汇总生成完成（博客资讯）

📊 统计:
- 日期: YYYY-MM-DD
- 博客资讯: M 篇

📁 文件路径:
- 本地: outputs/rss/daily-summary-blog-news-YYYY-MM-DD.md
- WPS云盘: CC-datas/rss/daily-summary-blog-news-YYYY-MM-DD.md
```

**全部为空时**：
```
📋 日报状态

API 调用成功！但当日（YYYY-MM-DD）暂无新文章。
- 期刊论文: 0 篇
- 博客资讯: 0 篇

是否需要查询其他日期？
- 指定日期：请提供日期（如 2026-02-12）
- 默认查询前一天：回复"前一天"或"昨天"
```

**可选**：预览 AI 总结的前几行

---

## 用户交互规则

### 当两个类型都返回 `empty` 状态

**禁止**自动传入新的日期参数重试。

**必须**询问用户（见上方"全部为空时"模板）。

### 当至少有一个类型返回 `success` 状态

1. 汇总所有成功生成的文件
2. 报告保存的文件路径和统计信息
3. 可选：预览 AI 总结的前几行
4. **不询问用户**，直接完成流程

### 部分成功、部分为空

- 正常报告成功生成的文件
- 提示哪些类型无文章（可选）
- 不询问用户，直接完成流程

---

## 参数参考

完整参数说明见 [API 规范](references/api-specification.md)

| 常用参数 | 说明 |
|----------|------|
| `--type` | **关键参数**：`journal`（期刊）或 `blog_news`（博客+新闻），详见 API 规范 |
| `--save`, `-s` | 保存为 markdown 文件 |
| `--date` | 指定日期 YYYY-MM-DD |
| `--limit` | 文章数量限制（默认 30） |
| `--output-dir`, `-o` | 自定义输出目录（默认：`$CLAUDE_PROJECT_DIR/outputs/rss`） |
| `--json` | 输出纯 JSON（调试用） |

---

## 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 无文章数据 | 询问用户是否查询其他日期 |
| WPS 上传失败 | 记录警告，不影响本地保存完成状态 |
| 连接失败 | 查阅 [troubleshooting.md](references/troubleshooting.md) |
| API 认证错误 | 检查 `scripts/.env` 配置 |

## 涉及的组件

| 组件 | 类型 | 角色 | 文件位置 |
|------|------|------|----------|
| `fetch-summary.py` | Script | RSS 数据获取和汇总 | `scripts/fetch-summary.py` |
| `wps-file-upload` | Skill | WPS 云盘上传 | `.claude/skills/wps-file-upload/SKILL.md` |

## 文件流程

```
并行调用两个脚本（journal + blog_news）
        ↓
    检查返回状态
        ↓
    仅处理成功的 → 生成独立 md 文件
        ├─ daily-summary-journal-YYYY-MM-DD.md
        └─ daily-summary-blog-news-YYYY-MM-DD.md
        ↓
批量上传到 WPS 云盘 (wps-file-upload skill, 路径: CC-datas/rss)
        ↓
汇总报告（统计 + 文件路径 + WPS 状态）
```

**关键改进**：
- ✅ 并行生成两类独立总结（提升效率）
- ✅ 仅生成有文章的类型（避免空文件）
- ✅ 分离文件命名，便于管理和检索
- ✅ 灵活上传，成功几个上传几个

## 参考文档

| 文档 | 内容 |
|------|------|
| [api-specification.md](references/api-specification.md) | API 规范、参数说明（包含 type 参数详解） |
| [troubleshooting.md](references/troubleshooting.md) | 故障排查指南 |
| [wps-file-upload](../wps-file-upload/SKILL.md) | WPS 云盘上传能力 |
