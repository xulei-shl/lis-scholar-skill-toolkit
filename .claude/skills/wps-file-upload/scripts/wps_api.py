#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS API 通用工具模块

提供 KSO-1 签名生成等通用功能
"""
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone


def get_rfc1123_date():
    """获取 RFC1123 格式的 UTC 时间"""
    return datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')


def generate_kso1_signature(client_secret, client_id, method, uri, content_type,
                           kso_date, params=None, request_body=""):
    """
    生成 KSO-1 签名

    Args:
        client_secret: 客户端密钥
        client_id: 客户端ID
        method: HTTP 方法 (GET/POST/PUT/DELETE等)
        uri: 请求 URI 路径 (如 /v7/drives)
        content_type: Content-Type 头
        kso_date: RFC1123 格式的日期时间
        params: 查询参数字典 (可选)
        request_body: 请求体内容 (可选)

    Returns:
        str: KSO-1 签名字符串，格式为 "KSO-1 {client_id}:{signature}"

    Example:
        >>> date = get_rfc1123_date()
        >>> sig = generate_kso1_signature(
        ...     "secret", "client_id", "GET", "/v7/drives",
        ...     "application/json", date, {"page_size": 100}
        ... )
    """
    # 计算 body 的 SHA256
    sha256_hex = ""
    if request_body:
        sha256_obj = hashlib.sha256()
        sha256_obj.update(request_body.encode("utf-8"))
        sha256_hex = sha256_obj.hexdigest()

    # 处理查询参数
    query_string = ""
    if params:
        # 对参数进行 URL 编码并排序（按key排序）
        sorted_params = sorted(params.items())
        query_string = "&".join([
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k, v in sorted_params
            if v is not None
        ])

    # 构建 URI（包含查询参数）
    if query_string:
        full_uri = f"{uri}?{query_string}"
    else:
        full_uri = uri

    # 生成签名字符串: KSO-1 + method + uri + content-type + date + body-sha256
    sign_str = "KSO-1" + method + full_uri + content_type + kso_date + sha256_hex

    # 使用 HMAC-SHA256 生成签名
    mac = hmac.new(
        bytes(client_secret, "utf-8"),
        bytes(sign_str, "utf-8"),
        hashlib.sha256
    )
    signature = mac.hexdigest()

    return f"KSO-1 {client_id}:{signature}"


def build_kso1_headers(client_secret, client_id, access_token, method, uri,
                       content_type="application/json", params=None, request_body="",
                       id_type="external"):
    """
    构建 KSO-1 签名的请求头

    Args:
        client_secret: 客户端密钥
        client_id: 客户端ID
        access_token: 访问令牌
        method: HTTP 方法
        uri: 请求 URI 路径
        content_type: Content-Type 头
        params: 查询参数字典 (可选)
        request_body: 请求体内容 (可选)
        id_type: X-Kso-Id-Type 头值 (internal/external)

    Returns:
        dict: 包含所有必要头的字典
    """
    kso_date = get_rfc1123_date()
    kso_authorization = generate_kso1_signature(
        client_secret, client_id, method, uri, content_type,
        kso_date, params, request_body
    )

    return {
        "Content-Type": content_type,
        "Authorization": f"Bearer {access_token}",
        "X-Kso-Date": kso_date,
        "X-Kso-Authorization": kso_authorization,
        "X-Kso-Id-Type": id_type
    }
