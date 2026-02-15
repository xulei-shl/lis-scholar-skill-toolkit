#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 文件上传模块

实现根据路径查找文件夹ID和完整的文件上传功能（三步上传流程）

参考文档:
- docs/文件/文件传输/请求文件上传信息.md
- docs/文件/文件传输/上传实体文件.md
- docs/文件/文件传输/提交文件上传完成.md
"""
import logging
import requests
import hashlib
import sys
from pathlib import Path

# 导入配置和工具函数
from wps_login import WPS_CONFIG, load_token, is_token_expired
from wps_api import build_kso1_headers
from wps_drives import get_all_drives
from wps_drives_files import get_children
from wps_create import create_folder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API 基础 URL
API_BASE_URL = "https://openapi.wps.cn"


def find_special_drive(access_token):
    """
    查找 source 为 special 的盘

    Returns:
        dict: 盘信息，如果未找到返回 None
    """
    drives = get_all_drives(
        access_token=access_token,
        allotee_type="user",
        sources=["special"]
    )

    for drive in drives:
        if drive.get("source") == "special":
            return drive

    return None


def resolve_path_to_folder_id(access_token, drive_id, path, parent_id="0"):
    """
    根据路径解析文件夹ID

    逐层查找路径中的每个文件夹，返回最终的文件夹ID

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        path: 文件夹路径，如 "CC-datas/gmail-daily" 或 ["CC-datas", "gmail-daily"]
        parent_id: 起始父目录ID，默认为 "0"（根目录）

    Returns:
        str: 最终文件夹的ID，如果路径不存在返回 None

    Example:
        >>> folder_id = resolve_path_to_folder_id(token, drive_id, "CC-datas/gmail-daily")
        >>> print(folder_id)  # 输出: "123456789"
    """
    # 处理路径格式
    if isinstance(path, str):
        # 分割路径，去除空白
        parts = [p.strip() for p in path.split("/") if p.strip()]
    elif isinstance(path, list):
        parts = [p.strip() for p in path if p.strip()]
    else:
        raise ValueError(f"不支持的路径类型: {type(path)}，期望 str 或 list")

    if not parts:
        return parent_id

    current_parent_id = parent_id

    for i, folder_name in enumerate(parts):
        logging.info(f"查找文件夹: {folder_name} (层级 {i+1}/{len(parts)})")

        # 获取当前目录下的子文件（只查文件夹）
        try:
            result = get_children(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=current_parent_id,
                page_size=500,
                filter_type="folder"
            )

            items = result.get("data", {}).get("items", [])

            # 查找匹配的文件夹
            found = False
            for item in items:
                if item.get("type") == "folder" and item.get("name") == folder_name:
                    current_parent_id = item.get("id")
                    logging.info(f"  找到: ID={current_parent_id}")
                    found = True
                    break

            if not found:
                logging.warning(f"文件夹 '{folder_name}' 不存在")
                return None

        except Exception as e:
            logging.error(f"查找文件夹 '{folder_name}' 时出错: {e}")
            return None

    return current_parent_id


def ensure_path_exists(access_token, drive_id, path, parent_id="0"):
    """
    确保路径存在，如果不存在则创建

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        path: 文件夹路径
        parent_id: 起始父目录ID

    Returns:
        str: 最终文件夹的ID

    Example:
        >>> folder_id = ensure_path_exists(token, drive_id, "CC-datas/gmail-daily")
        >>> # 如果路径不存在会自动创建
    """
    # 处理路径格式
    if isinstance(path, str):
        parts = [p.strip() for p in path.split("/") if p.strip()]
    elif isinstance(path, list):
        parts = [p.strip() for p in path if p.strip()]
    else:
        raise ValueError(f"不支持的路径类型: {type(path)}")

    if not parts:
        return parent_id

    current_parent_id = parent_id

    for i, folder_name in enumerate(parts):
        logging.info(f"检查文件夹: {folder_name} (层级 {i+1}/{len(parts)})")

        # 先尝试查找
        result = get_children(
            access_token=access_token,
            drive_id=drive_id,
            parent_id=current_parent_id,
            page_size=500,
            filter_type="folder"
        )

        items = result.get("data", {}).get("items", [])

        found = False
        for item in items:
            if item.get("type") == "folder" and item.get("name") == folder_name:
                current_parent_id = item.get("id")
                logging.info(f"  文件夹已存在: ID={current_parent_id}")
                found = True
                break

        if not found:
            # 需要创建文件夹
            logging.info(f"  文件夹不存在，正在创建...")
            folder_data = create_folder(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=current_parent_id,
                name=folder_name
            )
            current_parent_id = folder_data.get("id")
            logging.info(f"  文件夹已创建: ID={current_parent_id}")

    return current_parent_id


def request_upload_info(access_token, drive_id, parent_id, file_name, file_size,
                      file_id=None, hashes=None, on_name_conflict="rename"):
    """
    第一步：请求文件上传信息

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID
        file_name: 文件名（需带后缀）
        file_size: 文件大小（字节）
        file_id: 更新文件时指定文件ID
        hashes: 文件哈希信息 [{"type": "sha256", "sum": "..."}]
        on_name_conflict: 文件名冲突处理方式 (fail/rename/overwrite/replace)

    Returns:
        dict: 包含 upload_id 和上传地址的响应数据
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/request_upload"

    request_body = {
        "name": file_name,
        "size": file_size,
        "on_name_conflict": on_name_conflict
    }

    if file_id:
        request_body["file_id"] = file_id
    if hashes:
        request_body["hashes"] = hashes

    import json
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

    logging.info(f"请求上传信息: {file_name} ({file_size} 字节)")
    response = requests.post(url, headers=headers, data=body_str)

    result = response.json()

    if response.status_code != 200:
        raise Exception(f"请求上传信息失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"请求上传信息失败: {result.get('msg', 'Unknown error')}")

    return result.get("data", {})


def upload_file_to_storage(upload_url, upload_method, file_path, access_token):
    """
    第二步：上传实体文件到云存储

    Args:
        upload_url: 上传地址（从 request_upload_info 获取）
        upload_method: 上传方法（从 request_upload_info 获取）
        file_path: 本地文件路径
        access_token: 访问令牌

    Returns:
        str: etag 值（用于验证上传完整性）
    """
    with open(file_path, "rb") as f:
        file_content = f.read()

    logging.info(f"上传文件到云存储: {upload_url}")

    # 云存储上传也需要 Authorization 头
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.request(upload_method, upload_url, headers=headers, data=file_content)

    if response.status_code not in (200, 201):
        raise Exception(f"上传文件失败 (HTTP {response.status_code}): {response.text}")

    # etag 通常在响应头中
    etag = response.headers.get("etag", "")
    if etag:
        # 去除可能的引号
        etag = etag.strip('"')
        logging.info(f"上传成功，etag: {etag}")

    return etag


def commit_upload(access_token, drive_id, parent_id, upload_id):
    """
    第三步：提交文件上传完成

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        parent_id: 父目录ID
        upload_id: 上传标识（从 request_upload_info 获取）

    Returns:
        dict: 提交成功的响应数据
    """
    method = "POST"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/commit_upload"

    request_body = f'{{"upload_id":"{upload_id}"}}'

    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        request_body=request_body
    )

    url = API_BASE_URL + uri

    logging.info(f"提交上传完成: upload_id={upload_id}")
    response = requests.post(url, headers=headers, data=request_body)

    result = response.json()

    if response.status_code != 200:
        raise Exception(f"提交上传失败 (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"提交上传失败: {result.get('msg', 'Unknown error')}")

    return result.get("data", {})


def calculate_file_hashes(file_path):
    """
    计算文件的哈希值

    Args:
        file_path: 文件路径

    Returns:
        list: 哈希信息列表，包含 md5 和 sha256
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)

    return [
        {"type": "md5", "sum": md5_hash.hexdigest()},
        {"type": "sha256", "sum": sha256_hash.hexdigest()}
    ]


def upload_file(access_token, drive_id, file_path, target_path=None, parent_id=None,
               on_name_conflict="rename", create_path=False):
    """
    完整的文件上传流程（三步上传）

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘ID
        file_path: 本地文件路径
        target_path: 目标文件夹路径（如 "CC-datas/gmail-daily"）
                   如果指定，将根据路径查找 parent_id
        parent_id: 直接指定父目录ID（与 target_path 二选一）
        on_name_conflict: 文件名冲突处理方式 (fail/rename/overwrite/replace)
        create_path: 如果路径不存在是否自动创建

    Returns:
        dict: 上传成功的文件信息
    """
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_name = file_path_obj.name
    file_size = file_path_obj.stat().st_size

    # 解析目标 parent_id
    if target_path:
        if create_path:
            parent_id = ensure_path_exists(
                access_token=access_token,
                drive_id=drive_id,
                path=target_path,
                parent_id="0"
            )
        else:
            parent_id = resolve_path_to_folder_id(
                access_token=access_token,
                drive_id=drive_id,
                path=target_path,
                parent_id="0"
            )
            if parent_id is None:
                raise ValueError(f"路径不存在: {target_path}")
    elif not parent_id:
        # 未指定路径时，默认使用 CC-datas
        logging.info("未指定目标路径，使用默认路径: CC-datas")
        parent_id = ensure_path_exists(
            access_token=access_token,
            drive_id=drive_id,
            path="CC-datas",
            parent_id="0"
        )

    if not parent_id:
        raise ValueError("必须指定 target_path 或 parent_id")

    # 计算哈希值（可选但推荐）
    hashes = calculate_file_hashes(file_path)
    logging.info(f"文件哈希: MD5={hashes[0]['sum'][:16]}... SHA256={hashes[1]['sum'][:16]}...")

    # 第一步：请求上传信息
    upload_info = request_upload_info(
        access_token=access_token,
        drive_id=drive_id,
        parent_id=parent_id,
        file_name=file_name,
        file_size=file_size,
        hashes=hashes,
        on_name_conflict=on_name_conflict
    )

    upload_id = upload_info.get("upload_id")
    store_request = upload_info.get("store_request", {})

    if not upload_id:
        raise Exception("未获取到 upload_id")

    logging.info(f"获取到 upload_id: {upload_id}")

    # 第二步：上传实体文件
    upload_url = store_request.get("url")
    upload_method = store_request.get("method", "PUT")

    if not upload_url:
        raise Exception("未获取到上传地址")

    etag = upload_file_to_storage(upload_url, upload_method, file_path, access_token)

    # 第三步：提交上传完成
    result = commit_upload(
        access_token=access_token,
        drive_id=drive_id,
        parent_id=parent_id,
        upload_id=upload_id
    )

    logging.info(f"上传成功! 文件ID: {result.get('id')}")
    return result


def main():
    """主函数"""
    # 加载 token
    token_data = load_token()
    if not token_data:
        print("错误: 未找到有效的 token 文件，请先运行 wps_login.py 进行授权")
        return 1

    # 检查 token 是否过期
    if is_token_expired(token_data, "access"):
        print("错误: Access token 已过期，请运行 wps_login.py 刷新 token")
        return 1

    access_token = token_data["token"]["access_token"]
    # print(f"使用 access_token: {access_token[:20]}...")  # 调试信息，注释

    # 解析命令行参数
    drive_id = None
    target_path = None
    parent_id = None
    local_file = None
    on_name_conflict = "rename"
    create_path = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--help" or arg == "-h":
            # 帮助信息已注释，不输出
            return 0
        elif arg == "--drive-id" and i + 1 < len(sys.argv):
            drive_id = sys.argv[i + 1]
            i += 1
        elif arg == "--path" and i + 1 < len(sys.argv):
            target_path = sys.argv[i + 1]
            i += 1
        elif arg == "--parent-id" and i + 1 < len(sys.argv):
            parent_id = sys.argv[i + 1]
            i += 1
        elif arg == "--file" and i + 1 < len(sys.argv):
            local_file = sys.argv[i + 1]
            i += 1
        elif arg == "--conflict" and i + 1 < len(sys.argv):
            on_name_conflict = sys.argv[i + 1]
            i += 1
        elif arg == "--create-path":
            create_path = True
        i += 1

    # 检查必需参数
    if not local_file:
        print("错误: 必须指定 --file 参数")
        return 1

    # 查找 special 盘
    if not drive_id:
        # print("\n查找 source 为 'special' 的盘...")  # 进度日志，注释
        special_drive = find_special_drive(access_token)
        if special_drive:
            drive_id = special_drive.get("id")
            drive_name = special_drive.get("name", "N/A")
            # print(f"找到盘: {drive_name} (ID: {drive_id})")  # 进度日志，注释
        else:
            print("错误: 未找到 source 为 'special' 的盘")
            return 1
    else:
        # print(f"\n使用指定的盘 ID: {drive_id}")  # 进度日志，注释
        pass

    try:
        result = upload_file(
            access_token=access_token,
            drive_id=drive_id,
            file_path=local_file,
            target_path=target_path,
            parent_id=parent_id,
            on_name_conflict=on_name_conflict,
            create_path=create_path
        )

        print("\n" + "="*60)
        print("上传成功!")
        print("="*60)
        print(f"文件ID: {result.get('id')}")
        print(f"文件名: {result.get('name')}")
        print(f"类型: {result.get('type')}")
        print(f"大小: {result.get('size')} 字节")
        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
