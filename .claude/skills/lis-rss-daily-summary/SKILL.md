---
name: lis-rss-daily-summary
description: 获取 lis-rss-api 每日文章汇总并保存为 markdown。当用户请求"每日总结"、"文章汇总"、"RSS digest"、"今天的文章"、"daily news"，或提及 "lis-rss"、"RSS articles"、"daily summary" 时使用。
allowed-tools: Bash, Write, Skill
user-invocable: true
---

# LIS RSS 每日汇总

## 核心工作流

### 步骤 1：调用脚本

```bash
python $CLAUDE_PROJECT_DIR/.claude/skills/lis-rss-daily-summary/scripts/fetch-summary.py --save
```

> **路径规范**：使用 `$CLAUDE_PROJECT_DIR` 环境变量，确保跨工作目录的可靠路径解析。

### 步骤 2：处理响应

| 状态 | 动作 |
|------|------|
| `success` | 已保存 markdown 到 `$CLAUDE_PROJECT_DIR/outputs/rss/daily-summary-YYYY-MM-DD.md` |
| `empty` | **询问用户**是否查询其他日期 |
| `error` | 查阅 [troubleshooting.md](references/troubleshooting.md) |

### 步骤 3：上传到 WPS 云盘

```python
# 获取脚本返回的本地文件路径
local_file = "$CLAUDE_PROJECT_DIR/outputs/rss/daily-summary-YYYY-MM-DD.md"

# 调用 wps-file-upload skill 上传到 CC-datas/rss 目录
wps_upload_result = Skill(
    skill="wps-file-upload",
    args=f"--file {local_file} --path CC-datas/rss --create-path"
)
```

**错误处理**：如果 WPS 上传失败，仅记录警告，不影响整体流程完成状态。本地文件始终保存成功。

### 步骤 4：报告结果（success 状态）

**输出模板**：

```
✅ RSS 每日汇总生成完成

📊 统计:
- 日期: YYYY-MM-DD
- 文章总数: X 篇
- 分类: 分类1 (Y篇), 分类2 (Z篇), ...

📁 文件路径:
- 本地: outputs/rss/daily-summary-YYYY-MM-DD[_n].md
- WPS云盘: CC-datas/rss/{文件名} (文件ID: {id}, 大小: {size} 字节)
```

上传失败时：
```
📁 文件路径:
- 本地: outputs/rss/daily-summary-YYYY-MM-DD[_n].md
- WPS云盘: 上传失败 - {错误原因}
```

**可选**：预览 AI 总结的前几行

---

## 用户交互规则

### 当返回 `empty` 状态

**禁止**自动传入新的日期参数重试。

**必须**询问用户：

```
API 调用成功！但当日（2026-02-13）暂无新文章。

是否需要查询其他日期？
- 指定日期：请提供日期（如 2026-02-12）
- 默认查询前一天：回复"前一天"或"昨天"
```

### 当返回 `success` 状态

脚本已自动保存 markdown 文件（使用 `--save` 参数）。
1. 报告保存的文件路径
2. 报告关键统计信息
3. 可选：预览 AI 总结的前几行

---

## 参数参考

完整参数说明见 [API 规范](references/api-specification.md)

| 常用参数 | 说明 |
|----------|------|
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
调用 fetch-summary.py --save
        ↓
生成 markdown → outputs/rss/daily-summary-YYYY-MM-DD.md
        ↓
上传到 WPS 云盘 (wps-file-upload skill, 路径: CC-datas/rss)
        ↓
报告结果（本地路径 + WPS 上传状态）
```

## 参考文档

| 文档 | 内容 |
|------|------|
| [api-specification.md](references/api-specification.md) | API 规范、参数说明 |
| [troubleshooting.md](references/troubleshooting.md) | 故障排查指南 |
| [wps-file-upload](../wps-file-upload/SKILL.md) | WPS 云盘上传能力 |
