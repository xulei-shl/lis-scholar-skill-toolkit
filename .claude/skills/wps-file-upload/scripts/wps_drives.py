#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取 WPS 云盘列表

参考文档: docs/云盘/盘列表.md
"""
import logging
import requests
import json
import sys
from pathlib import Path

# 导入配置和工具函数
from wps_login import WPS_CONFIG, load_token, is_token_expired
from wps_api import build_kso1_headers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API 基础 URL
API_BASE_URL = "https://openapi.wps.cn"


def get_drives(access_token, allotee_type="user", page_size=100, page_token=None,
              allotee_id=None, sources=None, with_ext_attrs=False):
    """
    获取盘列表

    Args:
        access_token: 访问令牌
        allotee_type: 盘归属身份类型，user-获取操作者自己的私有盘列表，
                      group-获取用户组下的盘列表，app-获取应用下的应用盘列表
        page_size: 分页大小，公网限制最大为500
        page_token: 分页token
        allotee_id: 盘归属身份id
        sources: 盘来源列表，如 ["special", "tmp", "secret", "feature"]
        with_ext_attrs: 是否获取盘扩展属性

    Returns:
        dict: 包含盘列表的响应数据
    """
    method = "GET"
    uri = "/v7/drives"

    # 构建查询参数
    params = {
        "allotee_type": allotee_type,
        "page_size": page_size,
    }

    if page_token:
        params["page_token"] = page_token
    if allotee_id:
        params["allotee_id"] = allotee_id
    if with_ext_attrs:
        params["with_ext_attrs"] = "true" if with_ext_attrs else "false"
    if sources:
        if isinstance(sources, list):
            params["sources"] = ",".join(sources)
        else:
            params["sources"] = sources

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


def get_all_drives(access_token, allotee_type="user", sources=None, with_ext_attrs=False):
    """
    获取所有盘（自动处理分页）

    Args:
        access_token: 访问令牌
        allotee_type: 盘归属身份类型
        sources: 盘来源列表
        with_ext_attrs: 是否获取盘扩展属性

    Returns:
        list: 所有盘的列表
    """
    all_drives = []
    page_token = None

    while True:
        result = get_drives(
            access_token=access_token,
            allotee_type=allotee_type,
            page_size=500,  # 使用最大分页大小
            page_token=page_token,
            sources=sources,
            with_ext_attrs=with_ext_attrs
        )

        items = result.get("data", {}).get("items", [])
        all_drives.extend(items)

        logging.info(f"获取到 {len(items)} 个盘，累计 {len(all_drives)} 个")

        # 检查是否有下一页
        next_page_token = result.get("data", {}).get("next_page_token")
        if not next_page_token:
            break
        page_token = next_page_token

    return all_drives


def format_drive_info(drive):
    """格式化单个盘的信息"""
    quota = drive.get("quota", {})
    used_mb = quota.get("used", 0) / (1024 * 1024)
    total_mb = quota.get("total", 0) / (1024 * 1024)
    remaining_mb = quota.get("remaining", 0) / (1024 * 1024)

    info = f"""
盘名称: {drive.get('name', 'N/A')}
盘ID: {drive.get('id', 'N/A')}
类型: {drive.get('allotee_type', 'N/A')}
来源: {drive.get('source', 'N/A')}
状态: {drive.get('status', 'N/A')}
创建时间: {drive.get('ctime', 'N/A')}
修改时间: {drive.get('mtime', 'N/A')}
描述: {drive.get('description', 'N/A')}
配额信息:
  已用: {used_mb:.2f} MB
  总容量: {total_mb:.2f} MB
  剩余: {remaining_mb:.2f} MB"""
    return info


def print_drives_summary(drives):
    """打印盘列表摘要"""
    print(f"\n{'='*60}")
    print(f"共找到 {len(drives)} 个盘")
    print(f"{'='*60}\n")

    for i, drive in enumerate(drives, 1):
        print(f"[{i}] {drive.get('name', 'N/A')} (ID: {drive.get('id', 'N/A')})")
        print(f"    类型: {drive.get('allotee_type', 'N/A')} | 来源: {drive.get('source', 'N/A')} | 状态: {drive.get('status', 'N/A')}")

        quota = drive.get("quota", {})
        used_mb = quota.get("used", 0) / (1024 * 1024)
        total_mb = quota.get("total", 0) / (1024 * 1024) if quota.get("total", 0) > 0 else 0
        if total_mb > 0:
            usage_percent = (used_mb / total_mb) * 100
            print(f"    容量: {used_mb:.2f} MB / {total_mb:.2f} MB ({usage_percent:.1f}%)")
        else:
            print(f"    容量: {used_mb:.2f} MB")
        print()


def save_drives_to_file(drives, filename="drives_list.json"):
    """保存盘列表到文件"""
    output_path = Path(__file__).parent / filename
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(drives, f, indent=2, ensure_ascii=False)
    print(f"盘列表已保存到: {output_path}")


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
    allotee_type = "user"
    sources = None
    with_ext_attrs = False
    output_file = None
    show_detail = False

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--help" or arg == "-h":
            print("获取 WPS 云盘列表")
            print("")
            print("用法: python wps_drives.py [选项]")
            print("")
            print("选项:")
            print("  --type TYPE         盘归属类型 (user/group/app)，默认: user")
            print("  --sources SOURCES   盘来源，逗号分隔，如: special,tmp,secret,feature")
            print("  --ext-attrs         获取盘扩展属性")
            print("  --output FILE       保存结果到文件")
            print("  --detail            显示详细信息")
            print("  --help, -h          显示帮助信息")
            print("")
            print("盘来源说明 (公网):")
            print("  special    我的云文档")
            print("  tmp        我的漫游箱")
            print("  secret     私密文件夹")
            print("  feature    签名团队")
            return 0
        elif arg == "--type" and i + 1 < len(sys.argv):
            allotee_type = sys.argv[i + 1]
            i += 1
        elif arg == "--sources" and i + 1 < len(sys.argv):
            sources = sys.argv[i + 1].split(",")
            i += 1
        elif arg == "--ext-attrs":
            with_ext_attrs = True
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 1
        elif arg == "--detail":
            show_detail = True
        i += 1

    print(f"\n获取盘列表...")
    print(f"  归属类型: {allotee_type}")
    if sources:
        print(f"  盘来源: {', '.join(sources)}")

    try:
        # 获取所有盘
        drives = get_all_drives(
            access_token=access_token,
            allotee_type=allotee_type,
            sources=sources,
            with_ext_attrs=with_ext_attrs
        )

        # 打印摘要
        print_drives_summary(drives)

        # 打印详细信息
        if show_detail:
            print("\n" + "="*60)
            print("详细信息")
            print("="*60)
            for i, drive in enumerate(drives, 1):
                print(f"\n--- 盘 {i} ---")
                print(format_drive_info(drive))

        # 保存到文件
        if output_file:
            save_drives_to_file(drives, output_file)
        else:
            save_drives_to_file(drives)

        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
