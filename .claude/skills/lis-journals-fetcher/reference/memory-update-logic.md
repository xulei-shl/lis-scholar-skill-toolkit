# MEMORY.md 更新逻辑

## 触发条件

仅当 `user_modified = true` 时执行（即用户在步骤 9.2 中选择了修改过滤标签）。

## 双向检测逻辑

检测用户修改类型，分别触发对应的更新模式：

```python
# 检测用户修改类型（需要对比修改前后的状态）
# 伪代码逻辑：
papers_before = load_json(file_path)  # paper-filter 标注后的状态
# ... 用户人工修改 ...
papers_after = load_json(file_path)   # 用户修改后的状态

# 检测"从相关改为不相关"的论文（AI 误判）
false_positives = [
    p for p_before, p_after in zip(papers_before, papers_after)
    if p_before['interest_match'] == True and p_after['interest_match'] == False
]

# 检测"从不相关改为相关"的论文（AI 漏判）
false_negatives = [
    p for p_before, p_after in zip(papers_before, papers_after)
    if p_before['interest_match'] == False and p_after['interest_match'] == True
]
```

## 处理策略

| 检测结果 | 触发操作 |
|---------|---------|
| 存在误判论文（false_positives） | 调用 memory-updater-agent 模式 D（提取排除关键词） |
| 存在漏判论文（false_negatives） | 调用 memory-updater-agent 模式 C（更新关注主题词） |
| 两者都存在 | 依次调用模式 D 和模式 C |

## 调用示例

```python
# 模式 D：提取排除关键词
Task(
    subagent_type="memory-updater-agent",
    description="提取排除关键词",
    prompt="使用模式 D，从 {期刊名} {年-期}.json 中提取排除关键词并更新 MEMORY.md"
)

# 模式 C：更新关注主题词
Task(
    subagent_type="memory-updater-agent",
    description="更新 MEMORY.md 研究关键词",
    prompt="使用模式 C，从 {期刊名} {年-期}.json 中提取关键词并更新 MEMORY.md"
)
```

## 相关文档

> memory-updater skill 详见：[.claude/skills/memory-updater/SKILL.md](../../../skills/memory-updater/SKILL.md)
