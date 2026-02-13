# Memos API Reference

Complete API parameter and response documentation for Memos API v1.

## Base URL Structure

```
{MEMOS_BASE_URL}/api/v1/{endpoint}
```

Example: `https://memos.example.com/api/v1/memos`

## Endpoints

### Create Memo

**Endpoint:** `POST /api/v1/memos`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | string | **Yes** | Memo content (supports Markdown) |
| `visibility` | string | No | Visibility level: `PRIVATE`, `PROTECTED`, `PUBLIC` (default: `PRIVATE`) |
| `resourceIdList` | array | No | Associated resource IDs |
| `relationList` | array | No | Related memos list |

**Response:**
```json
{
  "name": "memos/RyZJUmdLwCnDNMC2o4Vh",
  "state": "NORMAL",
  "content": "#inbox Memo content",
  "createTime": "2026-02-13T07:05:01Z",
  "updateTime": "2026-02-13T07:05:01Z",
  "visibility": "PRIVATE",
  "tags": ["inbox"]
}
```

### List Memos

**Endpoint:** `GET /api/v1/memos`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pageSize` | int | No | Number of memos per page (default: 50) |
| `pageToken` | string | No | Pagination token for next page |
| `filter` | string | No | Filter query (e.g., `row_status == "NORMAL"`) |

**Response:**
```json
{
  "memos": [
    {
      "name": "memos/RyZJUmdLwCnDNMC2o4Vh",
      "content": "#inbox Memo content",
      "createTime": "2026-02-13T07:05:01Z"
    }
  ],
  "nextPageToken": "next_page_token_string"
}
```

### Get Memo Details

**Endpoint:** `GET /api/v1/{name}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | **Yes** | Memo name (format: `memos/xxxxxx`) |

**Response:** Same as Create Memo response

### Update Memo

**Endpoint:** `PATCH /api/v1/{name}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | **Yes** | Memo name (format: `memos/xxxxxx`) |
| `content` | string | No | New memo content |
| `visibility` | string | No | New visibility level |
| `updateMask` | string | No | Fields to update (e.g., `content,visibility`) |

**Response:** Same as Create Memo response

### Delete Memo

**Endpoint:** `DELETE /api/v1/{name}`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | **Yes** | Memo name (format: `memos/xxxxxx`) |

**Response:**
```json
{
  "name": "memos/RyZJUmdLwCnDNMC2o4Vh"
}
```

## Visibility Levels

| Level | Description |
|-------|-------------|
| `PRIVATE` | Only visible to creator (default) |
| `PROTECTED` | Visible to logged-in users |
| `PUBLIC` | Visible to everyone |

## Tag Syntax

Tags in Memos use the `#` prefix in content:

```markdown
#inbox This is an inbox item
#programming #python Learning Python today
#idea 💡 New project idea
```

Tags are automatically extracted from content and stored in the `tags` array.

## Filter Query Syntax

When listing memos, use the `filter` parameter for advanced filtering:

```python
# Normal memos only
filter = 'row_status == "NORMAL"'

# Content contains keyword
filter = 'content.contains("keyword")'

# Specific visibility
filter = 'visibility == "PUBLIC"'
```

## Error Responses

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `400` | Bad Request (invalid parameters) |
| `401` | Unauthorized (invalid or missing access token) |
| `404` | Not Found (memo doesn't exist) |
| `500` | Internal Server Error |

## Name Format

Memos v0.22+ uses `name` field as memo identifier (format: `memos/xxxxxx`), not numeric `id`.

Example: `memos/RyZJUmdLwCnDNMC2o4ToVh`

## Authentication

All requests require Authorization header:

```
Authorization: Bearer memos_pat_your_token_here
```

Get your access token: Memos → Settings → Access Tokens → New
