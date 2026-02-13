# 响应格式详解

## data 对象结构

### 成功响应的 data 字段

```json
{
  "date": "2025-02-11",           // 汇总日期
  "totalArticles": 15,             // 文章总数
  "articlesByType": { ... },       // 按类型分组的文章
  "summary": "...",               // AI 生成的总结
  "generatedAt": "2025-02-11T10:30:00.000Z"  // 生成时间
}
```

### cached 字段

| 值 | 说明 |
|-----|------|
| `true` | 返回数据库缓存结果，未调用 LLM |
| `false` | 新生成结果，调用了 LLM |

**注意**: 缓存机制有助于节省 LLM 调用成本，同一天重复请求会返回缓存。

## articlesByType 结构

```json
{
  "journal": [
    {
      "id": 1,
      "title": "文章标题",
      "url": "https://example.com/article",
      "publishedAt": "2025-02-11T08:00:00.000Z",
      "authors": ["作者名"],
      "summary": "文章摘要"
    }
  ],
  "blog": [...],
  "news": [...]
}
```

### 文章对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | number | 文章 ID |
| `title` | string | 文章标题 |
| `url` | string | 文章链接 |
| `publishedAt` | string | 发布时间（ISO 8601） |
| `authors` | string[] | 作者列表 |
| `summary` | string | 文章摘要 |

## 文章类型

| 类型 | 说明 |
|------|------|
| `journal` | 期刊/学术论文 |
| `blog` | 博客文章 |
| `news` | 新闻文章 |

## 状态码

| status | 说明 | HTTP 状态码 |
|--------|------|-------------|
| `success` | 成功获取汇总 | 200 |
| `empty` | 当日无新文章 | 200 |
| `error` | 请求错误 | 400/401/500 等 |

## 常见错误消息

| error | 说明 | 解决方案 |
|-------|------|----------|
| `Invalid API key` | API Key 无效 | 检查 `CLI_API_KEY` 环境变量或 `--api-key` 参数 |
| `User not found` | 用户不存在 | 检查 `--user-id` 是否正确 |
| `Service unavailable` | 服务不可用 | 确认 lis-rss-api 服务是否运行 |
| `Connection refused` | 连接被拒绝 | 确认服务地址和端口（默认 8007） |
