---
name: qwen-vision
description: 调用通义千问VL模型分析截图，通过MCP tool analyze_screenshot自动调用
run_as: inline
---

# 千问识图 Skill

当用户发送图片（截图、照片等），自动通过 MCP tool `analyze_screenshot` 调用通义千问 VL 模型进行分析。

## 触发条件

以下任一情况自动触发：
- 用户消息中包含图片附件
- 用户要求分析 / 描述 / 识别某张图片
- 用户提到截图并给出文件路径

## 执行方式

**使用 MCP tool `analyze_screenshot`，不要使用 `run_command` 或 `python -c`。**

MCP tool 参数：
- `path`（必填）：图片的绝对路径
- `question`（可选）：分析问题。默认会自动描述图片内容，对 UI/截图会分析布局配色设计问题

调用示例（model 直接调用 MCP tool，无需用户确认）：
```
tool: analyze_screenshot
args: { "path": "/abs/path/to/image.png", "question": "描述这张图片" }
```

## 重要规则

1. **永远不要用 `run_command` 调千问 API** — MCP server 已经封装好了，直接调 tool 即可
2. 路径必须是**绝对路径**
3. 如果用户没有指定 question，使用默认描述即可
4. 将返回结果直接展示给用户，保持原样不要改写
5. 如果 tool 返回错误（如 API key 未设置），友好提示用户检查 `DASHSCOPE_API_KEY` 环境变量

## API Key 配置

用户需要自行设置环境变量（不在本 skill 中配置）：
- `DASHSCOPE_API_KEY` — 从 https://dashscope.console.aliyun.com/apiKey 获取
