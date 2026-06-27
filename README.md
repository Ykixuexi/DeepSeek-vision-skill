# qwen-vision-mcp

> 让 DeepSeek 通过通义千问 VL 模型「看懂」图片 — 全程无感，零确认弹窗

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io/)

## 这是什么？

一套组合方案，让 **Reasonix**（或其他支持 MCP 的 AI 编程助手）在用户发送图片时**自动**调用通义千问 VL 模型进行识图分析，**无需用户点击任何确认按钮**。

| 组件 | 作用 | 技术 |
|------|------|------|
| **MCP Server** (`vision_server.py`) | 封装千问 VL API，暴露 `analyze_screenshot` 工具 | Python stdlib 零依赖 |
| **Skill** (`skill/qwen-vision.md`) | 告诉 AI 何时触发、调用哪个 tool | Reasonix Skill（inline） |

### 为什么没有确认弹窗？

传统方案用 `python -c` → `run_command` 调 API → 触发 Reasonix 的安全确认弹窗。

本方案：**MCP server 常驻后台，网络请求发生在 server 进程内部**，AI 只是调用 MCP tool（无 `run_command`），因此**零弹窗、用户无感**。

```
用户发图 → AI 调 MCP tool analyze_screenshot → MCP Server → 千问 API → 返回结果
         └─ 无 run_command ─ 无弹窗 ─┘
```

## 效果演示

```
用户: [发送了一张网页截图]
AI:    这张网页采用了深色主题设计，主色调为 #1a1a2e 深蓝紫背景…
       布局采用左侧导航栏 + 右侧内容区的经典双栏结构…
       字体方面标题使用了 Noto Serif SC，正文使用 Inter…
```

## 前置要求

- **Python 3.9+**（无需 pip install，纯标准库）
- **通义千问 API Key** → [DashScope 控制台](https://dashscope.console.aliyun.com/apiKey) 免费注册
- **Reasonix**（或其他 MCP 兼容客户端）

## 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/Ykixuexi/DeepSeek-vision-skill.git
cd DeepSeek-vision-skill
```

### 2. 配置 API Key

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入你的千问 API Key
# DASHSCOPE_API_KEY=sk-your-api-key-here
```

**Windows (PowerShell):**
```powershell
copy .env.example .env
notepad .env
```

或者直接设置系统环境变量（推荐，重启后仍有效）：

**Windows:**
```
setx DASHSCOPE_API_KEY "sk-your-api-key-here"
```

**macOS/Linux:**
```bash
echo 'export DASHSCOPE_API_KEY="sk-your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 注册 MCP Server 到 Reasonix

在 Reasonix 中执行（或手动添加到 `config.json` 的 `mcp` 数组）：

```
/mcp add vision -- python vision_server.py --cwd /path/to/qwen-vision-mcp
```

或者在 `config.json` 中手动添加：

```json
{
  "mcp": [
    "vision=python D:\\projects\\qwen-vision-mcp\\vision_server.py"
  ]
}
```

> **注意**：路径必须是**绝对路径**。Windows 用户如果装了多个 Python，可能需要写完整路径如 `C:\Python39\python.exe D:\...\vision_server.py`。

### 4. 安装 Skill

在 Reasonix 中执行（或手动复制到 `~/.reasonix/skills/`）：

```
/skill install D:\projects\qwen-vision-mcp\skill\qwen-vision.md
```

### 5. 重启 Reasonix

重启后新会话即可生效。

## 验证

发送一张图片给 Reasonix，观察：
1. **无确认弹窗** — AI 自动调用 `analyze_screenshot`
2. **返回分析结果** — 图片的内容描述

如果遇到问题：

| 现象 | 可能原因 | 解决 |
|------|----------|------|
| "API key not set" | 环境变量未生效 | 检查 `echo $DASHSCOPE_API_KEY`，必要时重启终端 |
| "File not found" | 路径不对 | 确认传给 tool 的是绝对路径 |
| "Unsupported format" | 图片格式不支持 | 支持 PNG/JPG/WebP/GIF/BMP |
| 超时 | 图片太大 | 默认 120s 超时，可在源码中调整 `TIMEOUT` |

## 项目结构

```
qwen-vision-mcp/
├── vision_server.py       # MCP Server（核心）
├── skill/
│   └── qwen-vision.md     # Reasonix Skill 定义
├── .env.example           # API Key 模板
├── setup.bat              # Windows 一键部署
├── setup.sh               # macOS/Linux 一键部署
├── .gitignore
├── LICENSE
└── README.md
```

## 工作原理

```
┌─────────────┐     MCP (stdio JSON-RPC)     ┌──────────────────┐
│  Reasonix   │ ◄──────────────────────────► │  vision_server   │
│             │   tools/list → [analyze_..]  │     .py          │
│  AI Model   │   tools/call → result        │                  │
│             │                               │  HTTP ──────────►│  DashScope
│  Skill      │   (告诉 AI 何时调哪个 tool)    │  ◄──────────────│  千问 VL
└─────────────┘                               └──────────────────┘
```

1. Skill 告诉 AI：「当用户发图片时，调用 `analyze_screenshot` tool」
2. AI 通过 MCP 协议调用 tool，参数 `{path, question}`
3. `vision_server.py` 读取图片 → base64 → HTTP POST → 千问 API
4. 返回文本结果，AI 展示给用户

全程**无 `run_command`**，**无确认弹窗**。

## API 费用

千问 VL Max 模型按 token 计费。一张典型截图（~500KB）约消耗 **0.01-0.03 元**。

参考：[DashScope 计费文档](https://help.aliyun.com/zh/model-studio/getting-started/models)

## FAQ

**Q: 为什么不用 `python -c` 直接调 API？**
A: `python -c` 走 `run_command`，Reasonix 检测到网络请求会弹确认窗。"无感"体验的核心就是绕过这个确认。

**Q: MCP server 会一直运行吗？**
A: MCP server 由 Reasonix 按需启动和管理，随会话结束自动关闭，不占用资源。

**Q: 支持哪些图片格式？**
A: PNG、JPG、JPEG、WebP、GIF、BMP。

**Q: 可以用其他 VL 模型吗？**
A: 可以。修改 `vision_server.py` 中的 `API_URL` 和 `MODEL` 常量即可切换到其他 OpenAI 兼容的 VL API。

**Q: API Key 安全吗？**
A: API Key 存在你的本地环境变量中，**不会**随 MCP server 或 skill 代码上传到任何地方。`.env` 文件已在 `.gitignore` 中排除。

## License

MIT
