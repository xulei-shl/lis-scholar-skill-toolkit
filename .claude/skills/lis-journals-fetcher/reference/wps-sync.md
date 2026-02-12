# WPS 云盘同步详细说明

## 重要

**仅当步骤 10 生成了总结报告（md 文件）时，才执行同步保存。JSON 文件不同步到 WPS 云盘。**

## 同步条件

| 条件 | 行为 |
|------|------|
| 用户在步骤 10 选择"跳过"（未生成总结报告） | 不执行同步 |
| 仅同步总结报告的 md 文件 | json 文件不同步 |

## 同步文件列表

| 文件类型 | 同步 | 本地路径 | 同步路径 |
|-----------|-------|-----------|----------|
| 原始数据（已标注） | ❌ | `outputs/{期刊名}/{年-期}.json` | - |
| 筛选文件 | ❌ | `outputs/{期刊名}/{年-期}-filtered.json` | - |
| 总结报告 | ✅ | `outputs/{期刊名}/{年-期}-summary.md` | `WPS云盘/.../lis-journals/{期刊名}/{年-期}-summary.md` |

## 同步路径常量

```
C:\Users\Administrator\WPSDrive\1568727350\WPS企业云盘\上海图书馆(上海科学技术情报研究所)\我的企业文档\CC-datas\lis-journals\{期刊名}\
```

## 实现逻辑

```python
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

# 仅同步总结报告（md 文件）
summary_file = Path("outputs/{期刊名}/{年-期}-summary.md")
if summary_file.exists():
    # 同步路径
    sync_base = Path(r"C:\Users\Administrator\WPSDrive\1568727350\WPS企业云盘\上海图书馆(上海科学技术情报研究所)\我的企业文档\CC-datas\lis-journals")
    sync_dir = sync_base / "{期刊名}"
    sync_dir.mkdir(parents=True, exist_ok=True)

    sync_path = sync_dir / f"{年-期}-summary.md"
    unique_sync_path = get_unique_path(sync_path)
    try:
        shutil.copy2(summary_file, unique_sync_path)
    except Exception as e:
        # 记录警告，不影响任务完成状态
        print(f"警告: 同步文件失败 {summary_file.name}: {e}")
else:
    # 未生成总结报告，跳过同步
    print("未生成总结报告，跳过 WPS 云盘同步")
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| 同步目录不存在或创建失败 | 仅记录警告 |
| 复制失败 | 仅记录警告，不影响任务完成状态 |
| 文件名冲突 | 自动添加 `_1`, `_2` 等后缀 |
