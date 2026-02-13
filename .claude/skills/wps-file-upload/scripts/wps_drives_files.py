#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 WPS 云盘文件列表

参考文档: docs/文件/文件夹/获取子文件列表.md
"""
import logging
import requests
import json
import sys
from pathlib import Path

# 导入配置和工具函数
from wps_login import WPS_CONFIG, load_token, is_token_expired
from wps_api import build_kso1_headers
from wps_drives import get_all_drives

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API 基础 URL
API_BASE_URL = "https://openapi.wps.cn"


def get_children(access_token, drive_id, parent_id="0", page_size=500, page_token=None,
                with_permission=False, with_ext_attrs=False, filter_exts=None,
                filter_type=None, order=None, order_by=None):
    """
    获取子文件列表

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘id
        parent_id: 文件夹id（根目录时为0）
        page_size: 分页大小，公网限制最大为500
        page_token: 分页token
        with_permission: 是否返回文件操作权限
        with_ext_attrs: 是否返回文件扩展属性
        filter_exts: 过滤条件,扩展名以英文逗号分隔
        filter_type: 按照文件类型筛选，例如：file、folder、shortcut等
        order: 排序方式：升序和降序 (desc, asc)
        order_by: 排序字段 (ctime, mtime, dtime, fname, fsize)

    Returns:
        dict: 包含文件列表的响应数据
    """
    method = "GET"
    uri = f"/v7/drives/{drive_id}/files/{parent_id}/children"

    # 构建查询参数
    params = {
        "page_size": page_size,
    }

    if page_token:
        params["page_token"] = page_token
    if with_permission:
        params["with_permission"] = "true" if with_permission else "false"
    if with_ext_attrs:
        params["with_ext_attrs"] = "true" if with_ext_attrs else "false"
    if filter_exts:
        params["filter_exts"] = filter_exts
    if filter_type:
        params["filter_type"] = filter_type
    if order:
        params["order"] = order
    if order_by:
        params["order_by"] = order_by

    # 使用统一的 API 工具构建请求头
    headers = build_kso1_headers(
        client_secret=WPS_CONFIG["client_secret"],
        client_id=WPS_CONFIG["client_id"],
        access_token=access_token,
        method=method,
        uri=uri,
        params=params
    )

    # 构建查询字符串（使用与签名相同的编码方式）
    import urllib.parse
    if params:
        sorted_params = sorted(params.items())
        query_string = "&".join([
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k, v in sorted_params
            if v is not None
        ])
        full_url = f"{API_BASE_URL}{uri}?{query_string}"
    else:
        full_url = API_BASE_URL + uri

    logging.info(f"Request URL: {full_url}")
    logging.info(f"Query params: {params}")

    response = requests.get(full_url, headers=headers)

    logging.info(f"Response status: {response.status_code}")

    result = response.json()

    if response.status_code != 200:
        raise Exception(f"Failed (HTTP {response.status_code}): {result}")
    if "code" in result and result["code"] != 0:
        raise Exception(f"Failed: {result.get('msg', 'Unknown error')}")
    if "error" in result:
        raise Exception(f"Failed: {result.get('error_description', result['error'])}")

    return result


def get_all_children(access_token, drive_id, parent_id="0", with_permission=False,
                    with_ext_attrs=False, filter_exts=None, filter_type=None,
                    order=None, order_by=None):
    """
    获取所有子文件（自动处理分页）

    Args:
        access_token: 访问令牌
        drive_id: 驱动盘id
        parent_id: 文件夹id
        with_permission: 是否返回文件操作权限
        with_ext_attrs: 是否返回文件扩展属性
        filter_exts: 过滤条件
        filter_type: 按照文件类型筛选
        order: 排序方式
        order_by: 排序字段

    Returns:
        list: 所有文件的列表
    """
    all_files = []
    page_token = None

    while True:
        result = get_children(
            access_token=access_token,
            drive_id=drive_id,
            parent_id=parent_id,
            page_size=500,
            page_token=page_token,
            with_permission=with_permission,
            with_ext_attrs=with_ext_attrs,
            filter_exts=filter_exts,
            filter_type=filter_type,
            order=order,
            order_by=order_by
        )

        items = result.get("data", {}).get("items", [])
        all_files.extend(items)

        logging.info(f"获取到 {len(items)} 个文件，累计 {len(all_files)} 个")

        # 检查是否有下一页
        next_page_token = result.get("data", {}).get("next_page_token")
        if not next_page_token:
            break
        page_token = next_page_token

    return all_files


def format_file_info(file):
    """格式化单个文件的信息"""
    size = file.get("size", 0)
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size / 1024:.2f} KB"
    elif size < 1024 * 1024 * 1024:
        size_str = f"{size / (1024 * 1024):.2f} MB"
    else:
        size_str = f"{size / (1024 * 1024 * 1024):.2f} GB"

    info = f"""
文件名: {file.get('name', 'N/A')}
文件ID: {file.get('id', 'N/A')}
类型: {file.get('type', 'N/A')}
大小: {size_str}
父目录ID: {file.get('parent_id', 'N/A')}
创建时间: {file.get('ctime', 'N/A')}
修改时间: {file.get('mtime', 'N/A')}"""

    if file.get("type") == "folder":
        info += f"\n链接ID: {file.get('link_id', 'N/A')}"

    return info


def print_files_summary(files):
    """打印文件列表摘要"""
    print(f"\n{'='*60}")
    print(f"共找到 {len(files)} 个项目")
    print(f"{'='*60}\n")

    # 统计
    folders = [f for f in files if f.get("type") == "folder"]
    regular_files = [f for f in files if f.get("type") != "folder"]
    print(f"文件夹: {len(folders)} 个")
    print(f"文件: {len(regular_files)} 个\n")

    for i, file in enumerate(files, 1):
        file_type = file.get("type", "N/A")
        icon = "[DIR]" if file_type == "folder" else "[FILE]"

        size = file.get("size", 0)
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.1f} MB"

        print(f"[{i}] {icon} {file.get('name', 'N/A')}")
        print(f"    ID: {file.get('id', 'N/A')} | 类型: {file_type} | 大小: {size_str}")
        print()


def save_files_to_file(files, filename="drives_files_list.json"):
    """保存文件列表到文件"""
    output_path = Path(__file__).parent / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(files, f, indent=2, ensure_ascii=False)
    print(f"文件列表已保存到: {output_path}")


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
    print(f"使用 access_token: {access_token[:20]}...")

    # 解析命令行参数
    parent_id = "0"
    drive_id = None
    filter_exts = None
    filter_type = None
    order = None
    order_by = None
    output_file = None
    show_detail = False
    with_permission = False
    with_ext_attrs = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--help" or arg == "-h":
            print("获取 WPS 云盘文件列表")
            print("")
            print("用法: python wps_files.py [选项]")
            print("")
            print("选项:")
            print("  --drive-id ID       指定盘ID（不指定则自动查找 special 盘）")
            print("  --parent-id ID      父目录ID，默认: 0（根目录）")
            print("  --filter-exts EXTS  过滤扩展名，逗号分隔，如: docx,xlsx,pdf")
            print("  --filter-type TYPE  过滤文件类型 (file/folder/shortcut)")
            print("  --order ORDER       排序方式 (asc/desc)")
            print("  --order-by FIELD    排序字段 (ctime/mtime/dtime/fname/fsize)")
            print("  --permission         获取文件操作权限")
            print("  --ext-attrs         获取文件扩展属性")
            print("  --output FILE       保存结果到文件")
            print("  --detail            显示详细信息")
            print("  --help, -h          显示帮助信息")
            return 0
        elif arg == "--drive-id" and i + 1 < len(sys.argv):
            drive_id = sys.argv[i + 1]
            i += 1
        elif arg == "--parent-id" and i + 1 < len(sys.argv):
            parent_id = sys.argv[i + 1]
            i += 1
        elif arg == "--filter-exts" and i + 1 < len(sys.argv):
            filter_exts = sys.argv[i + 1]
            i += 1
        elif arg == "--filter-type" and i + 1 < len(sys.argv):
            filter_type = sys.argv[i + 1]
            i += 1
        elif arg == "--order":
            order = sys.argv[i + 1] if i + 1 < len(sys.argv) else "desc"
            if i + 1 < len(sys.argv):
                i += 1
        elif arg == "--order-by":
            order_by = sys.argv[i + 1] if i + 1 < len(sys.argv) else "mtime"
            if i + 1 < len(sys.argv):
                i += 1
        elif arg == "--permission":
            with_permission = True
        elif arg == "--ext-attrs":
            with_ext_attrs = True
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 1
        elif arg == "--detail":
            show_detail = True
        i += 1

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
    else:
        print(f"\n使用指定的盘 ID: {drive_id}")

    print(f"获取父目录 {parent_id} 下的文件列表...")

    try:
        # 获取所有文件
        files = get_all_children(
            access_token=access_token,
            drive_id=drive_id,
            parent_id=parent_id,
            with_permission=with_permission,
            with_ext_attrs=with_ext_attrs,
            filter_exts=filter_exts,
            filter_type=filter_type,
            order=order,
            order_by=order_by
        )

        # 打印摘要
        print_files_summary(files)

        # 打印详细信息
        if show_detail:
            print("\n" + "="*60)
            print("详细信息")
            print("="*60)
            for i, file in enumerate(files, 1):
                print(f"\n--- 文件 {i} ---")
                print(format_file_info(file))

        # 保存到文件
        if output_file:
            save_files_to_file(files, output_file)
        else:
            save_files_to_file(files)

        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
