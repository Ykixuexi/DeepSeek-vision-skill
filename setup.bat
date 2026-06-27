@echo off
chcp 65001 >nul
echo ============================================
echo   qwen-vision-mcp — Windows 部署脚本
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo        下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [√] Python 已安装
python --version

:: Check API Key
if "%DASHSCOPE_API_KEY%"=="" (
    echo.
    echo [!] 未检测到 DASHSCOPE_API_KEY 环境变量
    echo.
    echo 请选择配置方式:
    echo   1. 手动创建 .env 文件（当前目录下）
    echo   2. 设置系统环境变量（推荐，永久生效）
    echo.

    if not exist .env (
        echo [操作] 从 .env.example 创建 .env ...
        copy .env.example .env >nul
        echo [√] .env 已创建，请编辑它填入你的 API Key
        echo.
        echo    获取 Key: https://dashscope.console.aliyun.com/apiKey
        echo    编辑:   notepad .env
        echo.
    ) else (
        echo [√] .env 已存在，确认其中 API Key 正确即可
    )

    echo [提示] 或者用系统环境变量（重启后仍有效）:
    echo    setx DASHSCOPE_API_KEY "sk-your-api-key-here"
    echo.
) else (
    echo [√] DASHSCOPE_API_KEY 已设置
)

:: Get current directory (absolute path)
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo.
echo ============================================
echo   MCP Server 路径: %PROJECT_DIR%\vision_server.py
echo ============================================
echo.
echo 下一步 — 在 Reasonix 中注册 MCP Server:
echo.
echo   方式1 (推荐): 在 Reasonix 中输入:
echo     /mcp add vision -- python "%PROJECT_DIR%\vision_server.py"
echo.
echo   方式2: 编辑 config.json，在 "mcp" 数组中添加:
echo     "vision=python %PROJECT_DIR:\=\\%\\vision_server.py"
echo.
echo 然后安装 Skill:
echo   /skill install %PROJECT_DIR%\skill\qwen-vision.md
echo.
echo 最后重启 Reasonix 即可生效!
echo.
pause
