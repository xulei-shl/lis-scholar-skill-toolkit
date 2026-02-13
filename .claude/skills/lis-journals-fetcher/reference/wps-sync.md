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
| 总结报告 | ✅ | `outputs/{期刊名}/{年-期}-summary.md` | `CC-datas/lis-journals/{期刊名}/{年-期}-summary.md` |

## 实现逻辑

使用 `wps-file-upload` skill 进行文件上传，该 skill 会自动处理：
- 登录和 token 刷新
- 路径解析和创建（`--create-path` 参数）
- 文件上传和错误处理

```python
from pathlib import Path

# 仅同步总结报告（md 文件）
summary_file = Path("outputs/{期刊名}/{年-期}-summary.md")
if summary_file.exists():
    # 调用 wps-file-upload skill 上传到指定路径
    # wps-file-upload skill 会自动处理：登录、token刷新、路径创建、文件上传、同名文件冲突
    wps_upload_result = Skill(
        skill="wps-file-upload",
        args=f"--file {summary_file} --path CC-datas/lis-journals/{期刊名} --create-path"
    )
    # wps_upload_result 包含上传结果（文件ID、名称、大小）
    # 如果上传失败，wps-file-upload skill 会返回错误信息，在此记录警告即可
else:
    # 未生成总结报告，跳过同步
    print("未生成总结报告，跳过 WPS 云盘同步")
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| Token 过期 | wps-file-upload skill 自动刷新 |
| 同步路径不存在 | `--create-path` 参数自动创建 |
| 文件名冲突 | wps-file-upload skill 自动处理（rename 行为） |
| 上传失败 | 仅记录警告，不影响任务完成状态 |

## 参考

- [wps-file-upload skill 文档](../../wps-file-upload/SKILL.md)
