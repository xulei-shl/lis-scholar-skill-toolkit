#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WPS 云盘工具主入口

整合所有 WPS 操作功能，自动处理 token 验证和刷新

子命令:
    login      - 登录授权
    drives     - 列出所有盘
    files      - 列出文件/文件夹
    upload     - 上传文件
    create     - 新建文件/文件夹
    token      - 查看 token 状态
"""
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def ensure_valid_token():
    """
    确保获取有效的 access_token
    当 token 无效时，自动触发重新授权流程

    Returns:
        tuple: (access_token, token_data)
            - access_token: 有效的访问令牌
            - token_data: 完整的 token 数据

    Raises:
        Exception: 如果无法获取有效 token
    """
    from wps_login import get_valid_token, save_token

    # 使用 wps_login 的智能 token 管理函数
    # 它会自动处理：有效检查、刷新、过期重新授权
    token_data, is_new = get_valid_token(force_refresh=False, code=None)

    # 如果是新获取或刷新的 token，保存到文件
    if is_new:
        save_token(token_data)

    return token_data["token"]["access_token"], token_data


def cmd_login(args):
    """登录授权"""
    from wps_login import main as login_main
    return login_main()


def cmd_drives(args):
    """列出所有盘"""
    access_token, _ = ensure_valid_token()

    from wps_drives import main as drives_main
    # 修改 sys.argv 以传递参数
    original_argv = sys.argv
    try:
        sys.argv = ["wps_drives.py"]
        if args.allotee_type:
            sys.argv.extend(["--allotee-type", args.allotee_type])
        if args.sources:
            sys.argv.extend(["--sources", args.sources])
        return drives_main()
    finally:
        sys.argv = original_argv


def cmd_files(args):
    """列出文件/文件夹"""
    access_token, _ = ensure_valid_token()

    from wps_drives_files import main as files_main
    original_argv = sys.argv
    try:
        sys.argv = ["wps_drives_files.py"]
        if args.drive_id:
            sys.argv.extend(["--drive-id", args.drive_id])
        if args.parent_id:
            sys.argv.extend(["--parent-id", args.parent_id])
        if args.filter_exts:
            sys.argv.extend(["--filter-exts", args.filter_exts])
        if args.filter_type:
            sys.argv.extend(["--filter-type", args.filter_type])
        if args.order:
            sys.argv.extend(["--order", args.order])
        if args.order_by:
            sys.argv.extend(["--order-by", args.order_by])
        if args.permission:
            sys.argv.append("--permission")
        if args.ext_attrs:
            sys.argv.append("--ext-attrs")
        if args.detail:
            sys.argv.append("--detail")
        if args.output:
            sys.argv.extend(["--output", args.output])
        return files_main()
    finally:
        sys.argv = original_argv


def cmd_upload(args):
    """上传文件"""
    access_token, _ = ensure_valid_token()

    from wps_upload import upload_file, find_special_drive

    # 查找 special 盘
    drive_id = args.drive_id
    if not drive_id:
        logging.info("查找 source 为 'special' 的盘...")
        special_drive = find_special_drive(access_token)
        if special_drive:
            drive_id = special_drive.get("id")
            drive_name = special_drive.get("name", "N/A")
            logging.info(f"找到盘: {drive_name} (ID: {drive_id})")
        else:
            raise Exception("未找到 source 为 'special' 的盘")

    # 默认自动创建路径，除非指定 --no-create-path
    create_path = not args.no_create_path

    result = upload_file(
        access_token=access_token,
        drive_id=drive_id,
        file_path=args.file,
        target_path=args.path,
        parent_id=args.parent_id,
        on_name_conflict=args.conflict or "rename",
        create_path=create_path
    )

    print("\n" + "=" * 60)
    print("上传成功!")
    print("=" * 60)
    print(f"文件ID: {result.get('id')}")
    print(f"文件名: {result.get('name')}")
    print(f"类型: {result.get('type')}")
    print(f"大小: {result.get('size')} 字节")
    return 0


def cmd_create(args):
    """新建文件/文件夹"""
    access_token, _ = ensure_valid_token()

    from wps_create import (
        create_folder, create_file, create_with_path, find_special_drive
    )

    # 查找 special 盘
    drive_id = args.drive_id
    if not drive_id:
        logging.info("查找 source 为 'special' 的盘...")
        special_drive = find_special_drive(access_token)
        if special_drive:
            drive_id = special_drive.get("id")
            drive_name = special_drive.get("name", "N/A")
            logging.info(f"找到盘: {drive_name} (ID: {drive_id})")
        else:
            raise Exception("未找到 source 为 'special' 的盘")

    parent_id = args.parent_id or "0"

    try:
        if args.parent_path:
            path_list = args.parent_path.split(",")
            result = create_with_path(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=args.name,
                file_type=args.type,
                on_name_conflict=args.conflict,
                parent_path=path_list
            )
        elif args.type == "folder":
            result = create_folder(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=args.name,
                on_name_conflict=args.conflict
            )
        elif args.type == "file":
            result = create_file(
                access_token=access_token,
                drive_id=drive_id,
                parent_id=parent_id,
                name=args.name,
                on_name_conflict=args.conflict
            )
        else:
            raise Exception(f"不支持的类型: {args.type}")

        print("\n" + "=" * 60)
        print("创建成功!")
        print("=" * 60)
        print(f"ID: {result.get('id')}")
        print(f"名称: {result.get('name')}")
        print(f"类型: {result.get('type')}")
        return 0

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_token(args):
    """查看 token 状态"""
    from wps_login import load_token, is_token_expired
    import time

    token_data = load_token()
    if not token_data:
        print("未找到 token 数据，请先运行: python main.py login")
        return 1

    token = token_data.get("token", {})
    obtained_at = token_data.get("_obtained_at", time.time())

    # 只输出简短状态，不输出详细信息
    # （主agent调用时不需要这些详细日志）
    access_token = token.get("access_token", "")
    if access_token:
        is_expired = is_token_expired(token_data, "access")
        status = "已过期" if is_expired else "有效"
        print(f"Access Token: {status}")

    refresh_token = token.get("refresh_token", "")
    if refresh_token:
        is_expired = is_token_expired(token_data, "refresh")
        status = "已过期" if is_expired else "有效"
        print(f"Refresh Token: {status}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="WPS 云盘工具 - 统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 登录授权
  python main.py login

  # 查看 token 状态
  python main.py token

  # 列出所有盘
  python main.py drives

  # 列出根目录文件
  python main.py files

  # 上传文件到指定路径（路径不存在会自动创建）
  python main.py upload --file test.docx --path CC-datas/gmail-daily

  # 上传文件到根目录下的新文件夹（不存在会自动创建）
  python main.py upload --file data.xlsx --path YYY

  # 上传文件但若路径不存在则报错
  python main.py upload --file test.pdf --path CC-datas/gmail-daily --no-create-path

  # 创建文件夹
  python main.py create --name "新文件夹" --type folder

  # 创建文件夹（带路径）
  python main.py create --name data --type folder --parent-path reports,2024
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # login 命令
    subparsers.add_parser("login", help="登录授权")

    # drives 命令
    parser_drives = subparsers.add_parser("drives", help="列出所有盘")
    parser_drives.add_argument("--allotee-type", default="user", help="分配类型")
    parser_drives.add_argument("--sources", help="筛选来源，逗号分隔")

    # files 命令
    parser_files = subparsers.add_parser("files", help="列出文件/文件夹")
    parser_files.add_argument("--drive-id", help="指定盘ID")
    parser_files.add_argument("--parent-id", default="0", help="父目录ID，默认0（根目录）")
    parser_files.add_argument("--filter-exts", help="过滤扩展名")
    parser_files.add_argument("--filter-type", help="过滤类型 (file/folder/shortcut)")
    parser_files.add_argument("--order", help="排序方式 (asc/desc)")
    parser_files.add_argument("--order-by", help="排序字段")
    parser_files.add_argument("--permission", action="store_true", help="获取操作权限")
    parser_files.add_argument("--ext-attrs", action="store_true", help="获取扩展属性")
    parser_files.add_argument("--detail", action="store_true", help="显示详细信息")
    parser_files.add_argument("--output", help="输出文件")

    # upload 命令
    parser_upload = subparsers.add_parser("upload", help="上传文件")
    parser_upload.add_argument("--file", required=True, help="本地文件路径（必须）")
    parser_upload.add_argument("--drive-id", help="指定盘ID")
    parser_upload.add_argument("--path", help="目标文件夹路径，如: CC-datas/gmail-daily")
    parser_upload.add_argument("--parent-id", help="直接指定父目录ID")
    parser_upload.add_argument("--conflict", choices=["fail", "rename", "overwrite", "replace"],
                           default="rename", help="文件名冲突处理方式")
    parser_upload.add_argument("--no-create-path", action="store_true",
                            help="如果路径不存在则报错（默认会自动创建）")

    # create 命令
    parser_create = subparsers.add_parser("create", help="新建文件/文件夹")
    parser_create.add_argument("--name", required=True, help="文件/文件夹名称（必须）")
    parser_create.add_argument("--type", choices=["folder", "file"], default="folder",
                            help="类型: folder/file，默认folder")
    parser_create.add_argument("--drive-id", help="指定盘ID")
    parser_create.add_argument("--parent-id", help="父目录ID，默认0（根目录）")
    parser_create.add_argument("--conflict", choices=["fail", "rename"],
                            help="文件名冲突处理方式")
    parser_create.add_argument("--parent-path", help="相对路径，逗号分隔，如: reports,2024")

    # token 命令
    subparsers.add_parser("token", help="查看 token 状态")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "login":
            return cmd_login(args)
        elif args.command == "drives":
            return cmd_drives(args)
        elif args.command == "files":
            return cmd_files(args)
        elif args.command == "upload":
            return cmd_upload(args)
        elif args.command == "create":
            return cmd_create(args)
        elif args.command == "token":
            return cmd_token(args)
        else:
            parser.print_help()
            return 0

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
