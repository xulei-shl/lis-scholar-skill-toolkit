[KSO-1 签名算法说明](https://365.kdocs.cn/3rd/open/documents/app-integration-dev/wps365/server/api-description/signature-description)
===============================================================================================================================

> **注意：** **KSO-1 签名仅在「开发者后台-安全设置-接口签名」开启签名时需要**

Header 说明
---------

| **Header 名称** | **参数类型** | **是否必填** | **说明** |
| --- | --- | --- | --- |
| Content-Type | string | 是 | 如：`application/json` |
| X-Kso-Date | string | 是 | RFC1123 格式的日期，例：`Wed, 23 Jan 2013 06:43:08 GMT` |
| X-Kso-Authorization | string | 是 | KSO-1 签名值。格式为：`KSO-1 accessKey:signature` |

> **X-Kso-Authorization 说明：**

1、`KSO-1`：签名算法版本，此处目前固定为 `KSO-1`（**注意：** 后面有一个空格）

2、`accessKey`：应用的 APPID（**注意：** 后面有一个英文冒号 `:`）

3、`signature`：使用 secretKey（应用 APPKEY） 作为密钥、SHA256 作为哈希算法， 通过 HMAC-SHA256 编码内容： `"KSO-1" + Method + RequestURI + ContentType + KsoDate + sha256(RequestBody)`

*   `"KSO-1"`：固定内容，签名版本字符串
*   `Method`：请求的方法
*   `RequestURI`：请求的 URI，包含 query 参数，例：`/v7/users?page_size=20&page_token=aabb`
*   `KsoDate`：RFC1123 格式的日期
*   `sha256(RequestBody)`：当请求体不为空时，使用 SHA256 哈希算法计算请求体的值

示例
--

### 示例 1

> 示例的 `RequestBody = ""`，为空

```
// 请求参数
accessKey = "AK123456"
secretKey = "sk098765"
Method = "GET"
RequestURI = "/v7/test?key=value"
ContentType = "application/json"
KsoDate = "Mon, 02 Jan 2006 15:04:05 GMT"
RequestBody = ""

// 计算结果
sha256(RequestBody) = ""
Content-Type = "application/json"
X-Kso-Date = "Mon, 02 Jan 2006 15:04:05 GMT"
X-Kso-Authorization = "KSO-1 AK123456:ce8df66877175e5198c8ea1362ffddf82e4941c6f25a4ca205a1ad09d0faaf03"
```

### 示例 2

> 示例的 `RequestBody = {"key": "value"}`，JSON 数据

```
// 请求参数
accessKey = "AK123456"
secretKey = "sk098765"
Method = "POST"
RequestURI = "/v7/test/body"
ContentType = "application/json"
KsoDate = "Mon, 02 Jan 2006 15:04:05 GMT"
RequestBody = `{"key": "value"}`            // 注意 json 格式，会影响到签名计算

// 计算结果
sha256(RequestBody) = "9724c1e20e6e3e4d7f57ed25f9d4efb006e508590d528c90da597f6a775c13e5"
Content-Type = "application/json"
X-Kso-Date = "Mon, 02 Jan 2006 15:04:05 GMT"
X-Kso-Authorization = "KSO-1 AK123456:c46e6c988130818ecba2484d51ac685948fbbef6814602c7874d6bfc41dc17b3"
```

Python 代码示例
-----------

### 签名方法示例

```
import hashlib
import hmac
import http

ACCESS_KEY = 'AK123456'
SECRET_KEY = 'sk098765'

def _get_kso1_signature(method, uri, content_type, kso_date, request_body):
    sha256_hex = ''
    if request_body is not None and len(request_body) > 0:
        sha256_obj = hashlib.sha256()
        sha256_obj.update(request_body.encode())
        sha256_hex = sha256_obj.hexdigest()

    mac = hmac.new(bytes(SECRET_KEY, 'utf-8'),
                   bytes('KSO-1' + method + uri + content_type + kso_date + sha256_hex, 'utf-8'),
                   hashlib.sha256)
    return mac.hexdigest()

def kso1_sign(method, uri, content_type, kso_date, request_body):
    kso_signature = _get_kso1_signature(method, uri, content_type, kso_date, request_body)
    authorization = 'KSO-1 {}:{}'.format(ACCESS_KEY, kso_signature)
    return {
        'X-Kso-Date': kso_date,
        'X-Kso-Authorization': authorization
    }


if __name__ == '__main__':
    def test():
        method = http.HTTPMethod.POST
        uri = '/v7/test/body'
        content_type = 'application/json'
        kso_date = 'Mon, 02 Jan 2006 15:04:05 GMT'
        request_body = '{"key": "value"}'

        res = kso1_sign(method, uri, content_type, kso_date, request_body)
        print(res)


    test()
```