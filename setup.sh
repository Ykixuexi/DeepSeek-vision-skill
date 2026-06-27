#!/usr/bin/env bash
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BOLD}============================================${NC}"
echo -e "${BOLD}  qwen-vision-mcp — macOS/Linux 部署脚本${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[错误] 未找到 Python3，请先安装 Python 3.9+${NC}"
    exit 1
fi
echo -e "${GREEN}[√]${NC} Python 已安装: $(python3 --version)"

# Check API Key
if [ -z "${DASHSCOPE_API_KEY:-}" ]; then
    echo ""
    echo -e "${YELLOW}[!]${NC} 未检测到 DASHSCOPE_API_KEY 环境变量"
    echo ""

    if [ ! -f .env ]; then
        echo -e "[操作] 从 .env.example 创建 .env ..."
        cp .env.example .env
        echo -e "${GREEN}[√]${NC} .env 已创建，请编辑它填入你的 API Key"
        echo ""
        echo "    获取 Key: https://dashscope.console.aliyun.com/apiKey"
        echo "    编辑:     nano .env   (或 vim .env)"
        echo ""
    else
        echo -e "${GREEN}[√]${NC} .env 已存在，确认 API Key 正确即可"
    fi

    echo -e "[提示] 永久设置环境变量 (添加到 ~/.bashrc 或 ~/.zshrc):"
    echo '  export DASHSCOPE_API_KEY="sk-your-api-key-here"'
    echo ""
else
    echo -e "${GREEN}[√]${NC} DASHSCOPE_API_KEY 已设置"
fi

# Get absolute project directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "  MCP Server 路径: ${PROJECT_DIR}/vision_server.py"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "下一步 — 在 Reasonix 中注册 MCP Server:"
echo ""
echo "  方式1 (推荐): 在 Reasonix 中输入:"
echo "    /mcp add vision -- python3 ${PROJECT_DIR}/vision_server.py"
echo ""
echo "  方式2: 编辑 config.json，在 \"mcp\" 数组中添加:"
echo "    \"vision=python3 ${PROJECT_DIR}/vision_server.py\""
echo ""
echo "然后安装 Skill:"
echo "  /skill install ${PROJECT_DIR}/skill/qwen-vision.md"
echo ""
echo "最后重启 Reasonix 即可生效!"
