---
name: memos-api
description: "Create, retrieve, update, and delete Memos memos (notes). Supports natural language operations like 'record in memos', 'search memos', 'find notes by tag', and full CRUD operations. Use when user mentions memos, 备忘录, #标签, or note management. Requires Python requests package and Memos instance with access token."
context: fork
agent: general-purpose
allowed-tools:
  - Bash(python*)
  - Bash(pip*)
user-invocable: true
disable-model-invocation: false
---

# Memos API

Execute Memos API operations through Python CLI. This skill runs in isolated context to minimize main conversation footprint.

> **⚠️ CRITICAL: Content Extraction Rule**
> When processing natural language requests, you MUST strip trigger words from the actual content:
> - `备注记录：` or `备注记录：` → **REMOVE**, only use text after it
> - `记录：` or `记录：` → **REMOVE**, only use text after it
> - `在memos中记录` → **REMOVE**, only use text after it
>
> **Example:**
> - User: "备注记录：许磊测试" → Command: `create "许磊测试"` (NOT "备注记录：许磊测试")
> - User: "记录：今天开会" → Command: `create "今天开会"` (NOT "记录：今天开会")

## Quick Start

### 1. Install Dependencies

```bash
pip install requests python-dotenv
```

### 2. Configure Connection

Create configuration file at `{baseDir}/scripts/.env`:

```bash
MEMOS_BASE_URL=https://your-memos-instance.com
MEMOS_ACCESS_TOKEN=memos_pat_your_token_here
```

**Getting your access token:**
1. Login to your Memos instance
2. Go to **Settings → Access Tokens**
3. Click **New Access Token**
4. Copy the generated token (format: `memos_pat_xxxxxxxx`)

### 3. Verify Configuration

```bash
python {baseDir}/scripts/memos_client.py list
```

If configured correctly, this will display your recent memos.

## Core Operations

| Operation | Command | Output |
|-----------|---------|--------|
| **Create** | `python {baseDir}/scripts/memos_client.py create "#inbox Content"` | Memo name |
| **Search** | `python {baseDir}/scripts/memos_client.py search "keyword"` | Matching memos |
| **By tag** | `python {baseDir}/scripts/memos_client.py tag inbox` | Tagged memos |
| **List** | `python {baseDir}/scripts/memos_client.py list --limit 10` | Recent memos |
| **Get detail** | `python {baseDir}/scripts/memos_client.py get memos/xxx` | Full memo |
| **Update** | `python {baseDir}/scripts/memos_client.py update memos/xxx "New"` | Updated memo |
| **Delete** | `python {baseDir}/scripts/memos_client.py delete memos/xxx` | Confirmation |

### Create Examples

```bash
# Basic memo
python {baseDir}/scripts/memos_client.py create "Simple note"

# With tag (use #tag in content)
python {baseDir}/scripts/memos_client.py create "#inbox Today's tasks"

# With visibility
python {baseDir}/scripts/memos_client.py create "Public note" --visibility PUBLIC

# Multi-line content
python {baseDir}/scripts/memos_client.py create "#meeting

## Attendees
- Alice
- Bob

## Notes
Discussed Q1 planning"
```

### Search Examples

```bash
# By keyword
python {baseDir}/scripts/memos_client.py search "Python"

# By tag
python {baseDir}/scripts/memos_client.py tag inbox

# List with JSON output
python {baseDir}/scripts/memos_client.py list --limit 20 --json
```

## Natural Language Triggers

### Core Principles

When interpreting user requests, follow these rules:

1. **Identify the intent** (create/search/update/delete) from trigger words
2. **Extract only the payload** - strip ALL trigger words and filler text
3. **Preserve the original meaning** - don't rephrase or summarize

### Trigger Patterns by Operation

**Create operations** - Remove these triggers and use what follows:
- `备注记录：` / `记录：` / `备忘：`
- `在memos中记录`
- `记录到备忘录`

**Search operations** - Extract the keyword/query:
- `搜索memos中关于...的笔记` → extract middle term
- `查找...相关内容` → extract subject
- `memos中有没有...` → extract search term

**Tag operations** - Extract tag name without `#`:
- `查找带有#...标签的备忘录` → extract tag name
- `#标签的笔记` → extract tag name

**Update/Delete** - These require memo name, usually from context or list result

### Examples

| User Input | Extracted Payload | Command |
|------------|------------------|---------|
| `备注记录：许磊skill记录测试` | `许磊skill记录测试` | create |
| `记录：今天的会议内容` | `今天的会议内容` | create |
| `在memos中记录项目计划` | `项目计划` | create |
| `搜索memos中关于Python的笔记` | `Python` | search |
| `查找带有#inbox标签的备忘录` | `inbox` | tag |
| `把这个想法记录到备忘录` | `这个想法` | create |
| `memos中最近的笔记有哪些？` | (none) | list |
| `memos中有没有关于AI的笔记？` | `AI` | search |

### Common Patterns

| Language Pattern | Trigger Word(s) to Remove |
|-----------------|--------------------------|
| Chinese create | `备注记录：`、`记录：`、`备忘：`、`在memos中记录` |
| Chinese search | `搜索memos中关于`、`的笔记`、`memos中有没有` |
| Chinese tag | `查找带有`、`标签的备忘录`、`#` |
| English create | `record in memos`、`create memo` |
| English search | `search memos for`、`find in memos` |

## Output Format

**Successful create:**
```
✅ Memo created successfully
   Name: memos/RyZJUmdLwCnDNMC2o4Vh
```

**Search results:**
```
Found 3 memo(s) matching 'Python':
  1. memos/Abc123: Python学习笔记 #programming...
  2. memos/Def456: Python API设计 #coding...
  3. memos/Ghi789: 使用Python处理数据 #data...
```

**List results:**
```
Recent 5 memo(s):
  1. memos/Xyz789: #inbox 今日待办...
  2. memos/Abc456: #reading 书籍推荐...
  3. memos/Def789: #idea 新项目构想...
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `❌ Configuration error: MEMOS_BASE_URL and MEMOS_ACCESS_TOKEN required` | Missing .env file | Create `{baseDir}/scripts/.env` with both variables |
| `❌ Authentication failed: Invalid access token` | Wrong token format | Verify token starts with `memos_pat_` |
| `❌ Connection failed: Cannot reach ...` | Server unreachable | Check MEMOS_BASE_URL is accessible |
| `❌ Not found: memos/xxx` | Invalid memo name | Use `list` command to find valid names |

## Resources

- **[API Reference](reference/api-reference.md)** - Complete API parameters and responses
- **[More Examples](reference/examples.md)** - Common workflows and batch operations
- **[Memos Official Docs](https://usememos.com/docs/api)** - Official API documentation

## Tools Reference

### memos_client.py

**Location:** `{baseDir}/scripts/memos_client.py`

**Usage:** `python memos_client.py <command> [options]`

**Commands:** `create`, `search`, `list`, `get`, `update`, `delete`, `tag`

**Environment variables:**
- `MEMOS_BASE_URL`: Your Memos instance URL (e.g., `https://memos.example.com`)
- `MEMOS_ACCESS_TOKEN`: Access token from Memos settings (format: `memos_pat_xxxxxxxx`)

**Dependencies:** `requests`, `python-dotenv`
