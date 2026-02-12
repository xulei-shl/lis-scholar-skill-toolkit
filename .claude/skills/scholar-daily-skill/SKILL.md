---
name: scholar-daily-skill
description: "自动处理 Google Scholar Alerts 邮件,基于 MEMORY.md 过滤论文,生成 Markdown 日报。使用场景:用户说'生成scholar日报'、'处理scholar邮件'、'今天的scholar日报',或使用/scholar-daily命令。"
allowed-tools: "Read, Write, Bash, Skill, Task, AskUserQuestion"
---

# Google Scholar 日报生成器

作为**主智能体（指挥官）**，协调 Gmail 访问、邮件解析、语义过滤和报告生成。

## 涉及的组件

| 组件 | 类型 | 角色 | 文件位置 |
|------|------|------|----------|
| `gmail-skill` | Skill | Gmail 访问工具 | `.claude/skills/gmail-skill/SKILL.md` |
| `scholar-email-processor` | Subagent | 邮件过滤专家 | `.claude/agents/scholar-email-processor.md` |
| `email_formatter.py` | Script | 邮件解析工具 | `.claude/skills/scholar-daily-skill/scripts/email_formatter.py` |

## 快速开始

```bash
# 生成今天的日报
/scholar-daily

# 生成指定日期的日报
/scholar-daily 2026-02-03
```

## 职责分工

| 组件 | 职责 | 读取文件 |
|------|------|----------|
| **主流程** | 编排任务、汇总结果、生成日报 | 仅读取子代理返回的 JSON 结果 |
| **Subagent** | 读取论文数据、读取研究兴趣、语义过滤 | `papers_*.json` + `MEMORY.md` |

**关键原则**：
- ✅ 主流程**不读取** `MEMORY.md` - 避免冗余和上下文浪费
- ✅ 子代理自主读取 `MEMORY.md` - 每个过滤任务独立完成
- ✅ 主流程只汇总子代理返回的 JSON 结果 - 保持简洁

## 工作流

### Step 1: 解析日期并搜索邮件

```bash
# 优先方案：使用 --date-range 参数（推荐）
# 该参数自动将日期转换为 Unix 时间戳，避免 PST 时区问题
# 注意：限定只搜索 Inbox 中的邮件
target_date="2026-02-04"
result=$(python .claude/skills/gmail-skill/scripts/gmail_skill.py search \
    "in:inbox from:scholaralerts-noreply@google.com" \
    --date-range "$target_date")

# 降级方案：如果当天无邮件，查询最新 6 封
if [ "$(echo $result | jq '.total')" -eq 0 ]; then
    result=$(python .claude/skills/gmail-skill/scripts/gmail_skill.py search \
        "in:inbox from:scholaralerts-noreply@google.com" \
        --max-results 6)
fi
```

### Step 2: 并行读取邮件（单条消息）

```bash
# 使用 --output 参数直接保存到 temps 目录
{baseDir}="项目根目录"
temps_dir="{baseDir}/outputs/temps"

# 在单条响应中并行调用多个 Bash
Bash(command=f"python ... read {id1} --output {temps_dir}/email_{id1}.json")
Bash(command=f"python ... read {id2} --output {temps_dir}/email_{id2}.json")
# ... 所有邮件
```

### Step 3: 并行解析论文（单条消息）

```bash
# 并行调用 email_formatter.py
Bash(command=f"python ... email_formatter.py {temps_dir}/email_{id1}.json --output {temps_dir}/papers_{id1}.md --json-output {temps_dir}/papers_{id1}.json")
Bash(command=f"python ... email_formatter.py {temps_dir}/email_{id2}.json --output {temps_dir}/papers_{id2}.md --json-output {temps_dir}/papers_{id2}.json")
# ... 所有邮件
```

**输出文件**：
- `papers_{id}.md` - Markdown 格式（人工查看用）
- `papers_{id}.json` - JSON 格式（过滤阶段用）

### Step 4: 并行过滤邮件

```
# 关键：并行启动 subagent
Task(
    subagent_type="scholar-email-processor",
    description=f"过滤邮件: {email1_subject}",
    prompt=f"""请过滤以下邮件中的相关论文:

邮件 ID: {email_id}
主题: {subject}

已解析论文文件: {temps_dir}/papers_{email_id}.json

任务:
1. 读取 {temps_dir}/papers_{email_id}.json 获取论文列表
2. 读取 {baseDir}/MEMORY.md 了解研究兴趣
3. 对每篇论文进行语义过滤,判断相关度
4. 返回 JSON 格式结果

论文已解析完成,无需调用 email_formatter.py。
"""
)

# 邮件2、3、4、5... 同样在同一条消息中并行调用
```

**重要提示**：
- 论文已在 Step 3 解析完成，subagent 只需读取 JSON
- Subagent 只负责过滤，不调用 `gmail read` 或 `email_formatter.py`

### Step 5: 汇总结果

此步骤只需处理Step 4子代理返回的 JSON 结果

```python
# 等待所有 subagent 完成，收集结果
total_emails = len(results)
total_papers = sum(r["total_papers"] for r in results)
relevant_papers = []
for r in results:
    relevant_papers.extend(r["relevant_papers"])

# 按相关度排序（星级从高到低）
def star_to_number(star_str):
    return star_str.count('★')

relevant_papers.sort(key=lambda x: star_to_number(x.get("relevance_score", "★☆☆☆☆")), reverse=True)
```

### Step 6: 生成日报

基于 Step 5 汇总的结果生成日报

日报包含三个章节：

1. **统计摘要** - 邮件数、论文数、相关论文数
2. **汇总摘要** - LLM 生成的综合性摘要（150-300字）
3. **相关论文详情** - 按相关度排序的论文列表

完整模板见 [REFERENCE.md](REFERENCE.md#日报模板)。

**保存路径**：
- 主路径：`{baseDir}/outputs/scholar-reports/scholar-report-YYYY-MM-DD.md`（如冲突自动添加 `_1`, `_2` 后缀）
- 同步路径：`C:\Users\Administrator\WPSDrive\...\gmail-daily\scholar-report-YYYY-MM-DD.md`（使用主路径的最终文件名）

```python
# 跨平台文件保存：先保存本地，再复制到同步目录
import shutil
from pathlib import Path

def get_unique_path(filepath: Path) -> Path:
    """如果文件已存在，添加后缀避免覆盖"""
    if not filepath.exists():
        return filepath
    counter = 1
    while True:
        new_path = filepath.with_stem(f"{filepath.stem}_{counter}")
        if not new_path.exists():
            return new_path
        counter += 1

# 1. 保存到本地（自动创建目录，处理文件名冲突）
report_dir = Path("{baseDir}") / "outputs" / "scholar-reports"
report_dir.mkdir(parents=True, exist_ok=True)
local_path = report_dir / f"scholar-report-{date}.md"
unique_local_path = get_unique_path(local_path)
# 写入日报内容到 unique_local_path

# 2. 复制到同步目录（自动创建目录，处理文件名冲突）
sync_dir = Path(r"C:\Users\Administrator\WPSDrive\1568727350\WPS企业云盘\上海图书馆(上海科学技术情报研究所)\我的企业文档\CC-datas\gmail-daily")
sync_dir.mkdir(parents=True, exist_ok=True)
sync_path = sync_dir / unique_local_path.name
unique_sync_path = get_unique_path(sync_path)
shutil.copy2(unique_local_path, unique_sync_path)
```

**错误处理**：如果同步目录不存在或复制失败，仅记录警告，不影响日报生成完成状态。

### Step 7: 删除已处理邮件

```bash
# 批量删除（使用逗号分隔多个 ID）
python .claude/skills/gmail-skill/scripts/gmail_skill.py trash "id1,id2,id3,id4"
```

**错误处理**：删除失败仅记录警告，不影响日报生成完成状态。

### Step 8: 清理临时文件

```bash
# 清理 temps 目录下的所有内容
rm -rf ${temps_dir}/*
```

## 输出格式

### 成功输出模板

```
✅ Scholar Alerts 日报生成完成

📊 统计:
- 处理邮件: X 封
- 总论文数: Y 篇
- 相关论文: Z 篇

📁 日报路径:
- 本地: outputs/scholar-reports/scholar-report-YYYY-MM-DD[_n].md
- 同步: WPS云盘\gmail-daily\scholar-report-YYYY-MM-DD[_n].md
```

### 高光论文（可选）

如果有 5 星论文，可以简要列出标题：

```
⭐ 今日高光论文:
- [论文标题1] (★★★★★)
- [论文标题2] (★★★★★)
```

**不要输出**：完整的论文列表、所有论文的详细摘要。

## 错误处理

| 错误类型 | 处理方式 |
|----------|----------|
| 无邮件 | 提示"未找到 {date} 的 scholaralerts 邮件" |
| Subagent 失败 | 记录错误,继续处理其他邮件 |
| 无相关论文 | 提示"今日无相关论文",生成空日报（仅统计摘要） |
| 删除邮件失败 | 记录警告,不影响日报生成 |

## 文件流程

```
Gmail search → 邮件 ID 列表
        ↓
并行读取 → outputs/temps/email_{id}.json
        ↓
并行解析 → outputs/temps/papers_{id}.md + papers_{id}.json
        ↓
并行过滤 → Subagent 读取 .json, 返回过滤结果
        ↓
汇总生成日报 → outputs/scholar-reports/scholar-report-YYYY-MM-DD.md
        ↓
复制日报 → WPS云盘同步目录 (gmail-daily/)
        ↓
删除已处理邮件（移到垃圾箱）
        ↓
清理 temps 目录
```

## 参考文档

| 文档 | 内容 |
|------|------|
| [REFERENCE.md](REFERENCE.md) | 日报模板、输出格式详细说明 |
| [CONFIG.md](CONFIG.md) | 常量定义、配置说明 |
| [gmail-skill](../gmail-skill/SKILL.md) | Gmail 访问能力 |
| [scholar-email-processor](../../agents/scholar-email-processor.md) | Subagent 详细说明 |
