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
  "limit": 30,            // 可选，默认 30
  "type": "journal"       // 可选，journal/blog_news
}
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `date` | string | 否 | 今天 | 日期格式 YYYY-MM-DD |
| `limit` | number | 否 | 30 | 最多包含的文章数量 |
| `type` | string | 否 | `null` | 总结类型：`journal`, `blog_news`，未指定则为综合 |

### type 参数详解

| 参数值 | 包含的源类型 | 说明 |
|--------|-------------|------|
| `journal` | `source_type = 'journal'` | 学术期刊论文（arXiv、Nature等） |
| `blog_news` | `source_type IN ('blog', 'news')` | 技术博客和新闻资讯 |
| 未指定 | 所有类型 | 综合总结（包含所有源类型） |

**示例**：

```bash
# 仅获取期刊论文总结
curl "http://localhost:8007/api/daily-summary/cli?user_id=1&api_key=mykey" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type": "journal", "limit": 30}'

# 仅获取博客资讯总结
curl "http://localhost:8007/api/daily-summary/cli?user_id=1&api_key=mykey" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"type": "blog_news", "limit": 50}'

# 获取综合总结（默认）
curl "http://localhost:8007/api/daily-summary/cli?user_id=1&api_key=mykey" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"limit": 30}'
```

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
