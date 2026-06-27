"""
Vision MCP Server — Qwen VL Image Analysis
===========================================
A lightweight MCP (Model Context Protocol) server that exposes the
`analyze_screenshot` tool backed by Alibaba's Qwen-VL (Vision Language) model.

Usage:
    python vision_server.py

Requirements:
    - Python 3.9+ (stdlib only — no pip install needed)
    - Environment variable: DASHSCOPE_API_KEY
      Get one at https://dashscope.console.aliyun.com/apiKey

Protocol: JSON-RPC 2.0 over stdio (MCP)
"""

import sys
import json
import base64
import os
import urllib.request
import urllib.error
import mimetypes
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL = "qwen-vl-max"
TIMEOUT = 120  # seconds — large images may take a while

# Supported image MIME types and their corresponding data-URI prefix
MIME_MAP = {
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif":  "image/gif",
    ".bmp":  "image/bmp",
}

DEFAULT_QUESTION = (
    "Describe this image in detail. If it's a UI/screenshot, analyze "
    "the layout, colors, typography, spacing, and any design issues."
)


# ── Helpers ─────────────────────────────────────────────────────────────────
def send(data: dict) -> None:
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def log(msg: str) -> None:
    """Log to stderr so it never mixes with JSON-RPC on stdout."""
    print(f"[vision-mcp] {msg}", file=sys.stderr)


def get_mime_type(path: str) -> str:
    """Determine MIME type from file extension. Falls back to image/png."""
    ext = Path(path).suffix.lower()
    return MIME_MAP.get(ext, "image/png")


def encode_image(path: str) -> str:
    """Base64-encode an image file. Returns the data URI string."""
    mime = get_mime_type(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"


def call_qwen(image_path: str, question: str) -> str:
    """
    Call the Qwen VL API with an image and question.
    Returns the model's text response.
    """
    if not API_KEY:
        raise RuntimeError(
            "DASHSCOPE_API_KEY environment variable is not set.\n"
            "Get your key at https://dashscope.console.aliyun.com/apiKey"
        )

    data_uri = encode_image(image_path)
    payload = json.dumps({
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ]
        }]
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API HTTP {e.code}: {detail[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")
    except TimeoutError:
        raise RuntimeError(f"Request timed out after {TIMEOUT}s")

    if "error" in body:
        raise RuntimeError(f"API error: {body['error'].get('message', body['error'])}")

    return body["choices"][0]["message"]["content"]


# ── JSON-RPC Handler ────────────────────────────────────────────────────────
def handle_request(msg: dict) -> None:
    rid = msg.get("id")
    method = msg.get("method", "")

    if method == "initialize":
        send({
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": "0.1",
                "serverInfo": {"name": "vision", "version": "1.0"},
                "capabilities": {},
            }
        })
        log("Initialized")

    elif method == "tools/list":
        send({
            "jsonrpc": "2.0", "id": rid,
            "result": {"tools": [{
                "name": "analyze_screenshot",
                "description": (
                    "Analyze an image using Qwen VL (Vision Language) model. "
                    "Supports screenshots, UIs, photos, and diagrams. "
                    "Returns a detailed description or answers specific questions about the image. "
                    "Supported formats: PNG, JPG, JPEG, WebP, GIF, BMP."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Absolute path to the image file on the local filesystem."
                        },
                        "question": {
                            "type": "string",
                            "description": (
                                "Question or instruction for the vision model. "
                                "Default: describe the image in detail, with UI/design analysis if applicable."
                            )
                        },
                    },
                    "required": ["path"],
                },
            }]},
        })

    elif method == "tools/call":
        args = msg.get("params", {}).get("arguments", {})
        path = args.get("path", "")
        question = args.get("question", DEFAULT_QUESTION)

        if not path:
            send({
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -1, "message": "Missing required parameter: path"}
            })
            return

        if not os.path.isfile(path):
            send({
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -2, "message": f"File not found: {path}"}
            })
            return

        ext = Path(path).suffix.lower()
        if ext not in MIME_MAP:
            send({
                "jsonrpc": "2.0", "id": rid,
                "error": {
                    "code": -3,
                    "message": f"Unsupported format '{ext}'. Supported: {', '.join(MIME_MAP)}"
                }
            })
            return

        try:
            result = call_qwen(path, question)
            send({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": result}]}
            })
        except Exception as e:
            log(f"Error: {e}")
            send({
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -4, "message": str(e)}
            })

    elif method == "notifications/initialized":
        pass  # MCP spec — no response needed

    else:
        send({"jsonrpc": "2.0", "id": rid, "result": {}})


# ── Main Loop ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"Starting — model={MODEL}, timeout={TIMEOUT}s")
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            log(f"Ignored invalid JSON: {line[:100]}")
            continue
        handle_request(msg)
