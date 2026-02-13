#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 新建文件/夹模块

参考文档: docs/文件/文件夹/新建文件（夹）.md
"""
import logging
import requests
import json
import sys

# 导入配置和工具函数
from wps_login import WPS_CONFIG, load_token, is_token_expired
from wps_api import build_kso1_headers
from wps_drives import get_all_drives

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API 基础 URL
API_BASE_URL = "https://openapi.wps.cn"


def find_special_drive(access_token):
    """查找 source 为 special 的盘"""
    drives = get_all_drives(
        access_token=access_token,
        allotee_type="user",
        sources=["special"]
    )
    for drive in drives:
        if drive.get("source") == "special":
            return drive
    return None


def create_folder(access_token, drive_id, parent_id, name, on_name_conflict=None):
    """
    创建文件夹

    参考文档: docs/文件/文件夹/新建文件（夹）.md

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID（根目录时为0）
        name: 文件夹名称
        on_name_conflict: 文件名冲突处理方式 (fail/rename)，默认不传为rename

    Returns:
        dict: 创建的文件夹信息
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/create"

    request_body = {
        "file_type": "folder",
        "name": name
    }

    if on_name_conflict:
        request_body["on_name_conflict"] = on_name_conflict

    body_str = json.dumps(request_body, separators=(',', ':'))

    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        request_body=body_str
    )

    url = API_BASE_URL + uri

    logging.info(f"创建文件夹: {name}")
    response = requests.post(url, headers=headers, data=body_str)
    result = response.json()

    if response.status_code != 200:
        raise Exception(f"创建文件夹失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"创建文件夹失败: {result.get('msg', 'Unknown error')}")

    folder_id = result.get("data", {}).get("id")
    logging.info(f"文件夹创建成功，ID: {folder_id}")

    return result.get("data", {})


def create_file(access_token, drive_id, parent_id, name, on_name_conflict=None):
    """
    创建空文件

    参考文档: docs/文件/文件夹/新建文件（夹）.md

    支持的格式: doc, docx, form, xls, otl, ppt, dbt, xlsx, pptx, pom, spt,
                dppt, link, resh, ckt, ddoc, dpdf, dxls, pof, wpsnote

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID
        name: 文件名（须带后缀）
        on_name_conflict: 文件名冲突处理方式

    Returns:
        dict: 创建的文件信息
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/create"

    request_body = {
        "file_type": "file",
        "name": name
    }

    if on_name_conflict:
        request_body["on_name_conflict"] = on_name_conflict

    body_str = json.dumps(request_body, separators=(',', ':'))

    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        request_body=body_str
    )

    url = API_BASE_URL + uri

    logging.info(f"创建文件: {name}")
    response = requests.post(url, headers=headers, data=body_str)
    result = response.json()

    if response.status_code != 200:
        raise Exception(f"创建文件失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"创建文件失败: {result.get('msg', 'Unknown error')}")

    return result.get("data", {})


def create_shortcut(access_token, drive_id, parent_id, name, source_file_id):
    """
    创建快捷方式

    参考文档: docs/文件/文件夹/新建文件（夹）.md

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID
        name: 快捷方式名称（须带 .link 后缀）
        source_file_id: 源文件ID

    Returns:
        dict: 创建的快捷方式信息
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/create"

    request_body = {
        "file_type": "shortcut",
        "name": name,
        "file_id": source_file_id
    }

    body_str = json.dumps(request_body, separators=(',', ':'))

    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        request_body=body_str
    )

    url = API_BASE_URL + uri

    logging.info(f"创建快捷方式: {name}")
    response = requests.post(url, headers=headers, data=body_str)
    result = response.json()

    if response.status_code != 200:
        raise Exception(f"创建快捷方式失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"创建快捷方式失败: {result.get('msg', 'Unknown error')}")

    return result.get("data", {})


def create_with_path(access_token, drive_id, parent_id, name, file_type,
                    on_name_conflict=None, parent_path=None):
    """
    创建文件/夹（支持 parent_path 自动创建路径）

    参考文档: docs/文件/文件夹/新建文件（夹）.md

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID
        name: 文件/文件夹名称
        file_type: 类型 (folder/file/shortcut)
        on_name_conflict: 文件名冲突处理方式
        parent_path: 相对路径数组，不存在会自动创建，如 ["reports", "2024"]

    Returns:
        dict: 创建的文件/文件夹信息
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/create"

    request_body = {
        "file_type": file_type,
        "name": name
    }

    if on_name_conflict:
        request_body["on_name_conflict"] = on_name_conflict
    if parent_path:
        request_body["parent_path"] = parent_path
    if file_type == "shortcut":
        # 快捷方式需要 file_id
        raise ValueError("快捷方式请使用 create_shortcut() 函数")

    body_str = json.dumps(request_body, separators=(',', ':'))

    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        request_body=body_str
    )

    url = API_BASE_URL + uri

    logging.info(f"创建 {file_type}: {name}")
    if parent_path:
        logging.info(f"  路径: /{'/'.join(parent_path)}")
    response = requests.post(url, headers=headers, data=body_str)
    result = response.json()

    if response.status_code != 200:
        raise Exception(f"创建失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"创建失败: {result.get('msg', 'Unknown error')}")

    return result.get("data", {})


def main():
    """主函数 - 命令行调用"""
    # 加载 token
    token_data = load_token()
    if not token_data:
        print("错误: 未找到有效的 token 文件，请先运行 wps_login.py 进行授权")
        return 1

    if is_token_expired(token_data, "access"):
        print("错误: Access token 已过期，请运行 wps_login.py 刷新 token")
        return 1

    access_token = token_data["token"]["access_token"]

    # 解析命令行参数
    drive_id = None
    parent_id = "0"
    name = None
    file_type = "folder"
    on_name_conflict = None
    parent_path = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--help" or arg == "-h":
            print("新建 WPS 文件/文件夹")
            print("")
            print("用法: python wps_create.py [选项]")
            print("")
            print("选项:")
            print("  --drive-id ID       指定盘ID（不指定则自动查找 special 盘）")
            print("  --parent-id ID      父目录ID，默认: 0（根目录）")
            print("  --name NAME         文件/文件夹名称（必须）")
            print("  --type TYPE         类型: folder/file/shortcut，默认: folder")
            print("  --conflict MODE     文件名冲突处理: fail/rename")
            print("  --parent-path PATH  相对路径数组，逗号分隔，如: reports,2024")
            print("  --help, -h          显示帮助信息")
            print("")
            print("示例:")
            print("  # 创建文件夹")
            print("  python wps_create.py --name \"我的文件夹\"")
            print("")
            print("  # 创建文件夹（带路径自动创建）")
            print("  python wps_create.py --name data --type folder --parent-path reports,2024")
            print("")
            print("  # 创建空文档")
            print("  python wps_create.py --name test.docx --type file")
            return 0
        elif arg == "--drive-id" and i + 1 < len(sys.argv):
            drive_id = sys.argv[i + 1]
            i += 1
        elif arg == "--parent-id" and i + 1 < len(sys.argv):
            parent_id = sys.argv[i + 1]
            i += 1
        elif arg == "--name" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            i += 1
        elif arg == "--type" and i + 1 < len(sys.argv):
            file_type = sys.argv[i + 1]
            i += 1
        elif arg == "--conflict" and i + 1 < len(sys.argv):
            on_name_conflict = sys.argv[i + 1]
            i += 1
        elif arg == "--parent-path" and i + 1 < len(sys.argv):
            parent_path = sys.argv[i + 1].split(",")
            i += 1
        i += 1

    # 检查必需参数
    if not name:
        print("错误: 必须指定 --name 参数")
        return 1

    # 查找 special 盘
    if not drive_id:
        print("\n查找 source 为 'special' 的盘...")
        special_drive = find_special_drive(access_token)
        if special_drive:
            drive_id = special_drive.get("id")
            drive_name = special_drive.get("name", "N/A")
            print(f"找到盘: {drive_name} (ID: {drive_id})")
        else:
            print("错误: 未找到 source 为 'special' 的盘")
            return 1

    try:
        if parent_path:
            result = create_with_path(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=name,
                file_type=file_type,
                on_name_conflict=on_name_conflict,
                parent_path=parent_path
            )
        elif file_type == "folder":
            result = create_folder(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=name,
                on_name_conflict=on_name_conflict
            )
        elif file_type == "file":
            result = create_file(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=name,
                on_name_conflict=on_name_conflict
            )
        else:
            print(f"错误: 不支持的类型 {file_type}")
            return 1

        print("\n" + "="*60)
        print("创建成功!")
        print("="*60)
        print(f"ID: {result.get('id')}")
        print(f"名称: {result.get('name')}")
        print(f"类型: {result.get('type')}")
        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
