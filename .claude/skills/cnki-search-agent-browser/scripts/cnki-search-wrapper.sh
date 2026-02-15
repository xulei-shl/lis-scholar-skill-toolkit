#!/bin/bash
# CNKI 检索环境自适应包装脚本
# 功能：自动检测运行环境，选择合适的执行方式（有/无图形界面）
# 用法: cnki-search-wrapper.sh [script_name] [args...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测是否需要 xvfb
need_xvfb() {
    # 检查操作系统
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        return 1  # 非 Linux 系统
    fi

    # 检查是否有 X Server（图形界面）
    if xhost > /dev/null 2>&1; then
        return 1  # 有图形界面
    fi

    # 无图形界面的 Linux 环境
    return 0
}

# 检查并安装 xvfb
ensure_xvfb() {
    if ! command -v xvfb-run &> /dev/null; then
        log_warn "xvfb 未安装，正在安装..."

        # 检测包管理器
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq
            sudo apt-get install -y xvfb
        elif command -v yum &> /dev/null; then
            sudo yum install -y xorg-x11-server-Xvfb
        else
            log_error "无法自动安装 xvfb，请手动安装"
            exit 1
        fi

        log_info "xvfb 安装完成"
    fi
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        log_error "用法: $0 <script_name> [args...]"
        echo ""
        echo "示例:"
        echo "  $0 cnki-search.sh \"人工智能\" 20"
        echo "  $0 cnki-adv-search.sh \"AI 伦理\" -s 2022 -e 2025 -c -n 20"
        exit 1
    fi

    SCRIPT_NAME="$1"
    shift
    ARGS=("$@")

    # 检查脚本是否存在
    if [ ! -f "$SCRIPT_DIR/$SCRIPT_NAME" ]; then
        log_error "脚本不存在: $SCRIPT_DIR/$SCRIPT_NAME"
        exit 1
    fi

    # 检测环境并执行
    if need_xvfb; then
        log_warn "检测到无图形界面环境，使用 xvfb-run"
        ensure_xvfb
        log_info "正在执行: bash $SCRIPT_NAME ${ARGS[*]}"
        xvfb-run -a bash "$SCRIPT_DIR/$SCRIPT_NAME" "${ARGS[@]}"
    else
        log_info "检测到图形界面环境，直接执行"
        log_info "正在执行: bash $SCRIPT_NAME ${ARGS[*]}"
        bash "$SCRIPT_DIR/$SCRIPT_NAME" "${ARGS[@]}"
    fi
}

main "$@"
