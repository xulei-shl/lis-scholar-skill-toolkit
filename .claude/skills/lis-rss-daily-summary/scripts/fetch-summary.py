#!/usr/bin/env python3
"""
LIS RSS Daily Summary Fetcher

直接调用 HTTP API 获取每日汇总，无需加载代码到上下文。
配置从 .env 文件读取，支持命令行参数覆盖。
"""
import requests
import sys
import argparse
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("错误: 缺少 python-dotenv 库", file=sys.stderr)
    print("请安装: pip install python-dotenv", file=sys.stderr)
    sys.exit(1)


def load_env_config():
    """加载 .env 配置"""
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)

    user_id = os.environ.get("LIS_RSS_USER_ID", "1")
    api_key = os.environ.get("LIS_RSS_API_KEY", "")
    base_url = os.environ.get("LIS_RSS_BASE_URL", "http://10.40.92.18:8007")

    try:
        user_id = int(user_id)
    except ValueError:
        user_id = 1

    return user_id, api_key, base_url


def fetch_summary(user_id: int, api_key: str, date: str = None, limit: int = 30,
                  base_url: str = "http://10.40.92.18:8007", summary_type: str = None):
    """获取每日汇总"""
    endpoint = f"{base_url}/api/daily-summary/cli"
    params = {"user_id": user_id, "api_key": api_key}
    body = {}

    if date:
        body["date"] = date
    if limit:
        body["limit"] = limit
    if summary_type:
        body["type"] = summary_type

    try:
        response = requests.post(endpoint, params=params, json=body, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"status": "error", "error": str(e)}


def pretty_print(result: dict):
    """美化输出结果"""
    if result.get("status") == "success":
        data = result.get("data", {})
        cached = " (缓存)" if result.get("cached") else " (新生成)"

        print(f" 日期: {data.get('date')}{cached}")
        print(f" 文章总数: {data.get('totalArticles')}")

        # 按类型统计
        by_type = data.get('articlesByType', {})
        if by_type:
            print("\n 分类:")
            type_names = {"journal": "期刊", "blog": "博客", "news": "新闻"}
            for t, articles in by_type.items():
                count = len(articles) if isinstance(articles, list) else 0
                print(f"   {type_names.get(t, t)}: {count} 篇")

        # 打印总结
        summary = data.get("summary")
        if summary:
            print(f"\n 总结:\n{summary}")

    elif result.get("status") == "empty":
        data = result.get("data", {})
        print(f" {result.get('message', '当日暂无通过审核的文章')}")
        print(f"   日期: {data.get('date')}")

    else:
        error = result.get('error', '未知错误')
        print(f" 错误: {error}", file=sys.stderr)


def generate_markdown(result: dict) -> str:
    """生成 markdown 格式报告"""
    if result.get("status") != "success":
        return ""

    data = result.get("data", {})
    date = data.get('date', '')
    total = data.get('totalArticles', 0)
    by_type = data.get('articlesByType', {})
    summary = data.get("summary", "")

    # 统计各类型数量
    type_names = {"journal": "期刊", "blog": "博客", "news": "新闻"}
    counts = {}
    for t in ["journal", "blog", "news"]:
        articles = by_type.get(t, [])
        counts[t] = len(articles) if isinstance(articles, list) else 0

    # 构建 markdown
    md_lines = [
        f"# LIS RSS 每日汇总 - {date}",
        "",
        "## 统计概览",
        f"- 日期: {date}",
        f"- 文章总数: {total}",
        f"- 分类: 期刊 {counts['journal']} 篇 | 博客 {counts['blog']} 篇 | 新闻 {counts['news']} 篇",
        "",
        "## AI 总结",
        "",
        summary,
        "",
        "## 文章列表",
        ""
    ]

    # 按类型添加文章列表
    for t in ["journal", "blog", "news"]:
        articles = by_type.get(t, [])
        if not articles or not isinstance(articles, list):
            continue

        md_lines.append(f"### {type_names.get(t, t)}")
        md_lines.append("")

        for article in articles:
            title = article.get("title", "无标题")
            url = article.get("url", "")
            article_summary = article.get("summary", "")
            authors = article.get("authors", [])
            author_str = ", ".join(authors) if authors else ""

            if url:
                md_lines.append(f"- [{title}]({url})")
            else:
                md_lines.append(f"- {title}")

            if author_str:
                md_lines.append(f"  - 作者: {author_str}")
            if article_summary:
                md_lines.append(f"  - 摘要: {article_summary}")

            md_lines.append("")

    return "\n".join(md_lines)


def save_markdown(content: str, date: str, output_dir: str = None, summary_type: str = None):
    """保存 markdown 文件"""
    # 检查内容是否为空
    if not content:
        print(" 提示: 无内容可保存", file=sys.stderr)
        return None

    # 检查是否仅为空内容框架（文章数为0）
    if "文章总数: 0" in content or '"totalArticles": 0' in content:
        print(" 提示: 当日无文章，跳过保存", file=sys.stderr)
        return None

    # 确定输出目录
    if output_dir is None:
        # 默认: 项目根目录 / outputs/rss
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent.parent  # 回到项目根目录
        output_dir = project_root / "outputs" / "rss"
    else:
        output_dir = Path(output_dir)

    # 创建目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 文件名（根据类型调整）
    if summary_type == "journal":
        filename = f"daily-summary-journal-{date}.md"
    elif summary_type == "blog_news":
        filename = f"daily-summary-blog-news-{date}.md"
    else:
        filename = f"daily-summary-{date}.md"

    filepath = output_dir / filename

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def main():
    # 从 .env 读取默认值
    default_user_id, default_api_key, default_base_url = load_env_config()

    parser = argparse.ArgumentParser(
        description="获取 LIS RSS 每日汇总",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
配置文件 .env:
  LIS_RSS_USER_ID=1
  LIS_RSS_API_KEY=your-key
  LIS_RSS_BASE_URL=http://10.40.92.18:8007

示例:
  %(prog)s                           # 使用 .env 配置
  %(prog)s --date 2025-02-11          # 指定日期
  %(prog)s -u 1 -k key --limit 50     # 覆盖配置
  %(prog)s --json                     # JSON 输出
  %(prog)s --save                     # 保存为 markdown 文件
  %(prog)s -s -o ./docs               # 保存到指定目录
  %(prog)s --type journal             # 仅生成期刊总结
  %(prog)s --type blog_news           # 仅生成博客资讯总结
        """
    )
    parser.add_argument("--user-id", "-u", type=int, default=default_user_id,
                       help=f"用户 ID (默认: {default_user_id})")
    parser.add_argument("--api-key", "-k", default=default_api_key,
                       help="API 密钥 (默认从 .env 读取)")
    parser.add_argument("--date", "-d", help="日期 (YYYY-MM-DD)")
    parser.add_argument("--limit", "-l", type=int, default=30, help="文章数量限制")
    parser.add_argument("--base-url", default=default_base_url,
                       help=f"服务地址 (默认: {default_base_url})")
    parser.add_argument("--type", "-t", choices=["journal", "blog_news"],
                       help="总结类型: journal=期刊, blog_news=博客+新闻")
    parser.add_argument("--json", action="store_true", help="输出纯 JSON")
    parser.add_argument("--pretty", "-p", action="store_true", help="美化输出")
    parser.add_argument("--save", "-s", action="store_true", help="保存为 markdown 文件")
    parser.add_argument("--output-dir", "-o", help="输出目录 (默认: 项目根目录/outputs/rss)")

    args = parser.parse_args()

    # 验证 API Key
    if not args.api_key:
        print(" 错误: 未提供 API Key", file=sys.stderr)
        print("   请在 .env 中设置 LIS_RSS_API_KEY 或使用 --api-key 参数", file=sys.stderr)
        sys.exit(1)

    # 默认使用美化输出（除非指定 --json）
    pretty = args.pretty if args.pretty is not None else (not args.json)

    result = fetch_summary(
        user_id=args.user_id,
        api_key=args.api_key,
        date=args.date,
        limit=args.limit,
        base_url=args.base_url,
        summary_type=args.type
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        pretty_print(result)

        # 保存 markdown 文件
        if args.save and result.get("status") == "success":
            md_content = generate_markdown(result)
            date = result.get("data", {}).get("date", "unknown")
            filepath = save_markdown(md_content, date, args.output_dir, args.type)
            if filepath:
                print(f"\n 已保存: {filepath}")

        # 退出码：success=0, empty=1, error=2
        if result.get("status") == "error":
            sys.exit(2)
        elif result.get("status") == "empty":
            sys.exit(1)


if __name__ == "__main__":
    main()
