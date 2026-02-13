# LIS RSS Daily Summary API 规范

## 端点

```
POST /api/daily-summary/cli
```

## 认证

查询参数（Query Parameters）：
- `user_id`: 用户 ID
- `api_key`: CLI API 密钥

## 请求体

```json
{
  "date": "2025-02-11",    // 可选，默认今天
  "limit": 30              // 可选，默认 30
}
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `date` | string | 否 | 今天 | 日期格式 YYYY-MM-DD |
| `limit` | number | 否 | 30 | 最多包含的文章数量 |

## 响应

### 成功 (200 OK)

```json
{
  "status": "success",
  "cached": false,
  "data": {
    "date": "2025-02-11",
    "totalArticles": 15,
    "articlesByType": {
      "journal": [...],
      "blog": [...],
      "news": [...]
    },
    "summary": "这是 AI 生成的当日文章总结...",
    "generatedAt": "2025-02-11T10:30:00.000Z"
  }
}
```

### 无新文章 (200 OK)

```json
{
  "status": "empty",
  "message": "当日暂无通过的文章",
  "data": {
    "date": "2025-02-11",
    "totalArticles": 0,
    "articlesByType": {
      "journal": [],
      "blog": [],
      "news": []
    }
  }
}
```

### 错误 (4xx/5xx)

```json
{
  "status": "error",
  "error": "Invalid API key"
}
```

## cURL 示例

```bash
curl "http://localhost:8007/api/daily-summary/cli?user_id=1&api_key=mykey" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"limit": 30}'
```

## 其他语言调用示例

### Python

```python
import requests

response = requests.post(
    "http://localhost:8007/api/daily-summary/cli",
    params={"user_id": 1, "api_key": "mykey"},
    json={"limit": 30}
)
result = response.json()

if result["status"] == "success":
    print(result["data"]["summary"])
elif result["status"] == "empty":
    print("无新文章")
else:
    print("错误:", result["error"])
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8007/api/daily-summary/cli?user_id=1&api_key=mykey', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ limit: 30 })
});
const result = await response.json();

if (result.status === 'success') {
  console.log(result.data.summary);
}
```
