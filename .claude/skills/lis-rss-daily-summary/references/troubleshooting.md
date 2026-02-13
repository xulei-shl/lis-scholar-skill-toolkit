# 问题排查指南

## 常见问题

### 连接失败

**错误信息**:
```
requests.exceptions.ConnectionError: Connection refused
```

**原因**: lis-rss-api 服务未运行或地址不正确

**解决方案**:
```bash
# 1. 检查服务是否运行
curl http://10.40.92.18:8007/health

# 2. 检查 .env 中的 LIS_RSS_BASE_URL 配置
cat .env | grep BASE_URL
```

---

### 认证失败

**错误信息**:
```json
{"status": "error", "error": "Invalid API key"}
```

**原因**: API Key 不正确或未配置

**解决方案**:
```bash
# 方式 1: 在 .env 中配置
echo "LIS_RSS_API_KEY=correct-key" >> .env

# 方式 2: 使用 --api-key 参数覆盖
python scripts/fetch-summary.py --api-key correct-key
```

**生成安全密钥**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 用户不存在

**错误信息**:
```json
{"status": "error", "error": "User not found"}
```

**原因**: 指定的 user_id 不存在

**解决方案**:
- 检查数据库中的用户 ID
- 确认使用正确的 user_id
- 默认测试用户 ID 通常是 1

---

### 无新文章（非错误）

**响应信息**:
```json
{"status": "empty", "message": "当日暂无通过的文章"}
```

**说明**: 这不是错误，表示当天确实没有新通过审核的文章

**注意事项**:
- 系统会自动检测，不会调用 LLM 生成空总结
- 这是正常行为，避免浪费 LLM 配额

---

### 日期格式错误

**错误信息**:
```
ValueError: Invalid date format, expected YYYY-MM-DD
```

**原因**: 日期格式不正确

**正确格式**: `2025-02-11`（年-月-日，使用连字符）

**解决方案**:
```bash
# 正确
python scripts/fetch-summary.py --user-id 1 --api-key key --date 2025-02-11

# 错误
python scripts/fetch-summary.py --user-id 1 --api-key key --date 2025/02/11
python scripts/fetch-summary.py --user-id 1 --api-key key --date 02-11
```

---

### 超时错误

**错误信息**:
```
requests.exceptions.Timeout: Request timed out
```

**原因**: 请求处理时间过长（通常是在生成 AI 总结时）

**解决方案**:
1. 检查 LLM 服务是否正常运行
2. 如果当天文章很多，生成总结可能需要更长时间
3. 可以使用 `--limit` 减少文章数量：
```bash
python scripts/fetch-summary.py --user-id 1 --api-key key --limit 10
```

---

### Python 脚本权限错误

**错误信息**（Linux/Mac）:
```
Permission denied: './scripts/fetch-summary.py'
```

**解决方案**:
```bash
chmod +x scripts/fetch-summary.py
```

---

### 环境变量不生效

**症状**: .env 文件配置后仍提示未提供 API Key

**排查步骤**:

1. 检查 .env 文件是否存在且格式正确：
```bash
cat .env
# 应该看到:
# LIS_RSS_USER_ID=1
# LIS_RSS_API_KEY=your-key
# LIS_RSS_BASE_URL=http://10.40.92.18:8007
```

2. 确保安装了 python-dotenv：
```bash
pip install python-dotenv
```

3. 检查脚本执行目录是否正确（应在 skill 目录下）

---

### 服务端口被占用

**错误信息**:
```
Error: listen EADDRINUSE: address already in use :::8007
```

**解决方案**:
```bash
# Linux/Mac
lsof -i :8007
kill -9 <PID>

# Windows
netstat -ano | findstr :8007
taskkill /PID <PID> /F
```

或修改 `.env` 中的 `PORT` 变量使用其他端口。

---

## 快速诊断检查清单

运行以下命令快速诊断：

```bash
# 1. 检查 Python 环境
python --version

# 2. 检查依赖库
python -c "import requests; print('requests OK')"
python -c "import dotenv; print('dotenv OK')"

# 3. 检查服务健康状态
curl http://10.40.92.18:8007/health

# 4. 检查 .env 配置
cat .env

# 5. 测试完整请求
python scripts/fetch-summary.py
```

---

## 获取帮助

如果以上方案都无法解决问题：

1. 检查 lis-rss-api 服务日志
2. 检查浏览器控制台（如果通过 Web 访问）
3. 查阅 [API 规范](api-specification.md) 确认接口使用方式
