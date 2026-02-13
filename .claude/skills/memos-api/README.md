# Memos API Skill

Memos API 的 Claude Code Skill，支持自然语言和命令行两种触发方式。

## 功能特性

- ✅ 创建、读取、更新、删除备忘录
- ✅ 按标签过滤和搜索
- ✅ 自动分页处理
- ✅ 支持 Markdown 格式
- ✅ 自然语言触发
- ✅ 独立上下文执行（不污染主对话）

## 快速开始

### 1. 配置环境

将配置模板复制为实际配置文件：

```bash
cp .claude/skills/memos-api/scripts/.env.example .claude/skills/memos-api/scripts/.env
```

编辑 `.env` 文件，填入你的 Memos 实例信息：

```bash
MEMOS_BASE_URL=https://your-memos-instance.com
MEMOS_ACCESS_TOKEN=memos_pat_your_token_here
```

### 2. 获取访问令牌

1. 登录你的 Memos 实例
2. 进入 **设置 → 访问令牌 (Access Tokens)**
3. 点击 **新建访问令牌**
4. 复制生成的令牌（格式如：`memos_pat_xxxxxxxxxxxx`）

### 3. 验证配置

```bash
python .claude/skills/memos-api/scripts/memos_client.py list
```

如果配置正确，将显示你最近的备忘录。

## 使用方式

### 自然语言触发

在与 Claude 对话时，可以直接使用自然语言：

| 触发方式 | 示例 |
|---------|------|
| 记录内容 | "在memos中记录今天的会议内容" |
| 搜索 | "搜索memos中关于Python的笔记" |
| 标签过滤 | "查找带有#inbox标签的备忘录" |
| 列出最近 | "memos中最近的笔记有哪些？" |

### 命令行触发

```bash
# 创建备忘录
python .claude/skills/memos-api/scripts/memos_client.py create "#inbox 今日待办"

# 搜索关键词
python .claude/skills/memos-api/scripts/memos_client.py search "Python"

# 按标签查询
python .claude/skills/memos-api/scripts/memos_client.py tag inbox

# 列出最近备忘录
python .claude/skills/memos-api/scripts/memos_client.py list --limit 10

# 获取详情
python .claude/skills/memos-api/scripts/memos_client.py get memos/xxx

# 更新备忘录
python .claude/skills/memos-api/scripts/memos_client.py update memos/xxx "新内容"

# 删除备忘录
python .claude/skills/memos-api/scripts/memos_client.py delete memos/xxx
```

### 斜杠命令触发

在 Claude Code 中输入 `/memos-api` 即可触发此技能。

## 目录结构

```
memos-api/
├── SKILL.md                  # 技能主文件
├── README.md                 # 中文说明（本文件）
├── reference/
│   ├── api-reference.md      # API 详细文档
│   └── examples.md           # 更多使用示例
└── scripts/
    ├── memos_client.py       # Python 客户端
    └── .env.example          # 配置模板
```

## 技术设计

- **上下文隔离**: 使用 `context: fork` 创建独立子代理，不占用主对话上下文
- **渐进披露**: 主文件精简 (<300行)，详细内容外链到 reference/
- **最小权限**: `allowed-tools` 限制为必要的 Python 执行权限

## 相关资源

- [Memos 官方文档](https://usememos.com/docs/api)
- [Memos GitHub 仓库](https://github.com/usememos/memos)
- [API 参考](reference/api-reference.md)
- [更多示例](reference/examples.md)

## 常见问题

### Q: 如何获取访问令牌？

**A:** 登录 Memos → 设置 → 访问令牌 → 新建访问令牌

### Q: 支持哪些可见性级别？

**A:** PRIVATE（仅自己可见）、PROTECTED（登录用户可见）、PUBLIC（所有人可见）

### Q: 如何使用标签？

**A:** 在内容中使用 `#标签名` 格式，如 `#inbox 今日待办`

### Q: 命令行输出 JSON 格式？

**A:** 添加 `--json` 参数，如 `list --json`
