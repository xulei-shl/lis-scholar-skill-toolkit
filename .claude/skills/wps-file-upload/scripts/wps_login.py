#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import requests
import urllib.parse
import json
import time
import webbrowser
from pathlib import Path

# 导入 WPS API 工具模块
from wps_api import build_kso1_headers

# 加载配置文件
def load_config():
    """从 .env 文件加载配置"""
    env_path = Path(__file__).parent / "config" / ".env"
    if not env_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在: {env_path}\n"
            f"请复制 .env.example 为 .env 并填入正确的配置值"
        )

    config = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            # 解析 key=value
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value.strip()

    # 映射环境变量到内部配置
    return {
        "client_id": config.get("WPS_CLIENT_ID", ""),
        "client_secret": config.get("WPS_CLIENT_SECRET", ""),
        "redirect_uri": config.get("WPS_REDIRECT_URI", ""),
        "scope": config.get("WPS_SCOPE", ""),
        "auth_url": config.get("WPS_AUTH_URL", ""),
        "token_url": config.get("WPS_TOKEN_URL", ""),
        "api_base_url": config.get("WPS_API_BASE_URL", ""),
        "user_info_url": config.get("WPS_USER_INFO_URL", ""),
    }

WPS_CONFIG = load_config()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def get_authorization_url():
    params = {"client_id": WPS_CONFIG["client_id"], "redirect_uri": WPS_CONFIG["redirect_uri"], "scope": WPS_CONFIG["scope"], "response_type": "code", "state": "wps_oauth_" + str(int(time.time()))}
    return WPS_CONFIG["auth_url"] + "?" + urllib.parse.urlencode(params)

def get_access_token(code):
    """使用授权码获取 access_token"""
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {"grant_type": "authorization_code", "client_id": WPS_CONFIG["client_id"], "client_secret": WPS_CONFIG["client_secret"], "code": code, "redirect_uri": WPS_CONFIG["redirect_uri"]}
    logging.info(f"Token URL: {WPS_CONFIG['token_url']}")
    logging.info(f"Request params: {params}")
    response = requests.post(WPS_CONFIG["token_url"], data=params, headers=headers)
    logging.info(f"Response status: {response.status_code}")
    logging.info(f"Response content: {response.text}")
    result = response.json()
    if response.status_code != 200: raise Exception(f"Failed (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0: raise Exception(f"Failed: {result.get('msg', 'Unknown error')}")
    if "error" in result: raise Exception(f"Failed: {result.get('error_description', result['error'])}")
    return result

def refresh_access_token(refresh_token):
    """使用 refresh_token 刷新 access_token"""
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    params = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": WPS_CONFIG["client_id"],
        "client_secret": WPS_CONFIG["client_secret"]
    }
    logging.info(f"Refreshing access_token...")
    response = requests.post(WPS_CONFIG["token_url"], data=params, headers=headers)
    result = response.json()
    if response.status_code != 200: raise Exception(f"Failed (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0: raise Exception(f"Failed: {result.get('msg', 'Unknown error')}")
    if "error" in result: raise Exception(f"Failed: {result.get('error_description', result['error'])}")
    return result

def get_token_file_path():
    """获取 token 文件路径"""
    return Path(__file__).parent / "data" / "token.json"

def load_token():
    """从文件加载 token 数据"""
    token_path = get_token_file_path()
    if not token_path.exists():
        return None
    try:
        with open(token_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError):
        return None

def save_token(token_data):
    """保存 token 到文件"""
    token_path = get_token_file_path()
    # 记录获取时间戳（用于后续检查过期）
    save_data = {
        k: v for k, v in token_data.items() if not k.startswith("_")
    }
    save_data["_obtained_at"] = time.time()
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

def is_token_expired(token_data, token_type="access"):
    """检查 token 是否过期"""
    if not token_data or "token" not in token_data:
        return True

    token = token_data["token"]
    expires_key = "expires_in" if token_type == "access" else "refresh_expires_in"

    if expires_key not in token:
        return True

    # 获取 token 时的 Unix 时间戳
    obtained_at = token_data.get("_obtained_at")
    if obtained_at is None:
        # 如果没有记录获取时间，使用文件修改时间作为回退方案
        token_path = get_token_file_path()
        if not token_path.exists():
            return True
        obtained_at = token_path.stat().st_mtime

    expires_in = token[expires_key]
    expire_time = obtained_at + expires_in

    # 留 60 秒缓冲时间
    return time.time() >= (expire_time - 60)

def get_valid_token(force_refresh=False, code=None):
    """
    获取有效的 token，智能处理刷新逻辑

    返回: (token_data, is_new_token)
        - token_data: 包含 token 和 user_info 的字典
        - is_new_token: 是否是新获取或刷新的 token
    """
    token_file_path = get_token_file_path()

    # 1. 如果强制刷新或没有 token 文件，执行完整授权流程
    if force_refresh or not token_file_path.exists():
        print("未找到有效的 token 文件，开始授权流程...")
        return perform_oauth_flow(code), True

    # 2. 加载已保存的 token
    token_data = load_token()
    if not token_data:
        print("Token 文件损坏或为空，开始授权流程...")
        return perform_oauth_flow(code), True

    # 3. 检查 access_token 是否过期
    if not is_token_expired(token_data, "access"):
        obtained_at = token_data.get("_obtained_at", time.time())
        expires_in = token_data["token"]["expires_in"]
        remaining_seconds = expires_in - (time.time() - obtained_at)
        print(f"✓ Access token 仍然有效（剩余约 {int(remaining_seconds / 60)} 分钟）")
        return token_data, False

    print("⚠ Access token 已过期，尝试使用 refresh_token 刷新...")

    # 4. 检查 refresh_token 是否过期
    if is_token_expired(token_data, "refresh"):
        print("⚠ Refresh token 也已过期，需要重新授权")
        return perform_oauth_flow(code), True

    # 5. 使用 refresh_token 刷新
    try:
        refresh_token = token_data["token"]["refresh_token"]
        print(f"使用 refresh_token: {refresh_token[:20]}...")
        new_token = refresh_access_token(refresh_token)

        print(f"✓ 刷新成功!")
        print(f"  新 Access Token: {new_token.get('access_token', '')[:20]}...")
        print(f"  有效期: {new_token.get('expires_in', 'Unknown')} 秒")

        # 保存新 token（保留 user_info）
        user_info = token_data.get("user_info")
        new_token_data = {"token": new_token, "user_info": user_info}
        save_token(new_token_data)

        return new_token_data, True
    except Exception as e:
        print(f"✗ 刷新失败: {e}")
        print("尝试重新授权...")
        return perform_oauth_flow(code), True

def get_user_info(access_token):
    method, uri = "GET", "/v7/users/current"
    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri
    )
    url = "https://openapi.wps.cn" + uri
    logging.info(f"User info URL: {url}")
    logging.info(f"Header X-Kso-Date: {headers['X-Kso-Date']}")
    logging.info(f"Header X-Kso-Authorization: {headers['X-Kso-Authorization'][:50]}...")
    response = requests.get(url, headers=headers)
    logging.info(f"Response status: {response.status_code}")
    logging.info(f"Response content: {response.text}")
    result = response.json()
    if response.status_code != 200: raise Exception(f"Failed (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0: raise Exception(f"Failed: {result.get('msg', 'Unknown error')}")
    if "error" in result: raise Exception(f"Failed: {result.get('error_description', result['error'])}")
    return result

def extract_code_from_url(url):
    if "?" not in url: return url.strip()
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    if "code" in params: return params["code"][0]
    raise Exception("No code parameter found in URL")

def perform_oauth_flow(code=None):
    print("=" * 50)
    print("WPS OA OAuth Authorization Flow")
    print("=" * 50)
    if code is None:
        print("[Step 1/3] Get authorization code")
        auth_url = get_authorization_url()
        print("Opening authorization page...")
        webbrowser.open(auth_url)
        print("Authorization page opened in browser")
        print("Please complete the following steps in browser:")
        print("  1. Login to WPS account (if not logged in)")
        print("  2. Click Agree to authorize button")
        print("  3. After authorization, the page will redirect")
        print("After redirect, please copy the complete URL from browser address bar, like:")
        print(f"  {WPS_CONFIG['redirect_uri']}?code=xxxxx&state=xxxxx")
        print("Then paste below (can paste full URL or just the code part):")
        input_str = input("Please enter authorization code or callback URL: ").strip()
        if not input_str: raise Exception("Authorization code cannot be empty")
        code = extract_code_from_url(input_str)
    print(f"Using authorization code: {code[:20]}...")
    print("[Step 2/3] Get access_token...")
    token_result = get_access_token(code)
    print(f"Access Token: {token_result.get('access_token', '')[:20]}...")
    print(f"Token Type: {token_result.get('token_type', 'Bearer')}")
    print(f"Expires In: {token_result.get('expires_in', 'Unknown')} seconds")
    if "refresh_token" in token_result: print(f"Refresh Token: {token_result['refresh_token'][:20]}...")
    access_token = token_result["access_token"]
    print("[Step 3/3] Get user information...")
    try:
        user_info = get_user_info(access_token)
        print("User information:")
        print(json.dumps(user_info, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error getting user info: {e}")
        user_info = None
    return {"token": token_result, "user_info": user_info}

def main():
    import sys

    # 解析命令行参数
    code = None
    force_refresh = False

    for arg in sys.argv[1:]:
        if arg == "--force" or arg == "-f":
            force_refresh = True
        elif arg == "--help" or arg == "-h":
            print("WPS OAuth Token 管理工具")
            print("")
            print("用法: python wps_login.py [选项] [code]")
            print("")
            print("选项:")
            print("  --force, -f    强制重新授权，忽略已保存的 token")
            print("  --help, -h     显示帮助信息")
            print("")
            print("参数:")
            print("  code           可选的授权码，如果提供则跳过浏览器打开步骤")
            print("")
            print("说明:")
            print("  - 程序会自动检查已保存的 token 是否有效")
            print("  - access_token 过期时，会使用 refresh_token 自动刷新")
            print("  - refresh_token 也过期时，才会要求重新授权")
            return 0
        else:
            code = arg

    try:
        result, is_new = get_valid_token(force_refresh, code)

        if is_new:
            save_token(result)
            print("✓ Token 已保存到 wps_token.json")
        else:
            print("✓ 使用已保存的有效 token")

        # 输出当前 token 状态
        token = result["token"]
        print("")
        print("当前 Token 状态:")
        print(f"  Access Token 有效期: {token.get('expires_in', 'Unknown')} 秒 (约 {token.get('expires_in', 0) // 3600} 小时)")
        if "refresh_expires_in" in token:
            refresh_days = token.get("refresh_expires_in", 0) // 86400
            print(f"  Refresh Token 有效期: 约 {refresh_days} 天")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
