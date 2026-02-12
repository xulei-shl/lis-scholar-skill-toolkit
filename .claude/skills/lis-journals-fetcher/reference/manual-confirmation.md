# 人工修改确认详细流程

## 注意

此步骤涉及交互式用户输入循环，**不适合并行执行**，必须保持同步等待用户响应。

## 数据处理要求

1. 使用 Read 工具读取完整的 JSON 文件
2. 解析每篇论文的实际状态（`interest_match`、`match_reasons`、`relevance_score`）
3. 动态生成过滤结果列表（按相关度排序）
4. 正确的编号映射（通过 `title` 或 `pages` 定位论文）

## 核心流程

```
1. 读取 JSON 文件
2. 解析论文状态，按相关度分组排序
3. 显示过滤结果：
   - 相关论文（按相关度排序）
   - 不相关论文（按相关度排序）
4. 收集用户输入（支持快捷语法）
5. 一次性读写执行批量修改
6. 重新显示修改后结果
```

## 快捷输入语法

| 输入格式 | 含义 | 示例 |
|---------|------|------|
| `keep: 2,3,4,5` | 只保留指定编号为相关，其他全改为不相关 | `keep: 2,3,4,5` |
| `set: 1,6,10` | 将指定编号设为相关，其他设为不相关 | `set: 1,6,10` |
| `2,3,4,5` | 等同于 `keep:` 语法 | `2,3,4,5` |
| `toggle: 1,6,10` | 切换指定编号的相关性状态 | `toggle: 1,6,10` |
| `无` / `跳过` | 不修改，继续下一步 | `无` |

## 批量修改逻辑

```python
# keep: 2,3,4,5 语法处理
if input.startswith("keep:") or input.startswith("set:"):
    keep_ids = parse_ids(input)
    papers = read_json(file_path)
    for i, paper in enumerate(papers, 1):
        paper['interest_match'] = (i in keep_ids)
    write_json(file_path, papers)

# toggle: 1,6,10 语法处理
elif input.startswith("toggle:"):
    toggle_ids = parse_ids(input)
    papers = read_json(file_path)
    for i, paper in enumerate(papers, 1):
        if i in toggle_ids:
            paper['interest_match'] = not paper['interest_match']
    write_json(file_path, papers)
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 编号超出范围 | 提示"编号无效，请输入1-N之间的编号" |
| JSON 格式损坏 | 提示错误并跳过该年期 |
