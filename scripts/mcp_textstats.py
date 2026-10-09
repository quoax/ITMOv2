#!/usr/bin/env python3
"""
Minimal MCP-like server over stdin/stdout exposing a single tool: textstats.
This is NOT a full MCP implementation; it speaks a tiny JSON-RPC subset:
- Request: {"id": <number|string>, "method": "tools/list"}
- Request: {"id": <...>, "method": "tools/call", "params": {"name": "textstats", "args": {"path": "..."}}}
Response mirrors the id and returns either {"result": ...} or {"error": {"code": 400, "message": "..."}}.

Tool: textstats(path)
- Counts lines, words, and characters in the given UTF-8 text file.

Run manually:
echo '{"id":1,"method":"tools/list"}' | python3 scripts/mcp_textstats.py
echo '{"id":2,"method":"tools/call","params":{"name":"textstats","args":{"path":"README.md"}}}' | python3 scripts/mcp_textstats.py
"""
import json
import sys
from pathlib import Path


def write(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def list_tools(req_id):
    return {
        "id": req_id,
        "result": [
            {
                "name": "textstats",
                "description": "Count lines, words, and characters in a UTF-8 text file",
                "args": {"path": "string"},
            }
        ],
    }


def call_textstats(req_id, args):
    if not isinstance(args, dict) or "path" not in args:
        return {"id": req_id, "error": {"code": 400, "message": "args.path is required"}}
    path = args["path"]
    if not isinstance(path, str) or not path.strip():
        return {"id": req_id, "error": {"code": 400, "message": "args.path must be a non-empty string"}}
    p = Path(path)
    if not p.exists():
        return {"id": req_id, "error": {"code": 404, "message": f"file not found: {path}"}}
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as e:
        return {"id": req_id, "error": {"code": 500, "message": f"failed to read file: {e}"}}
    # Simple stats: lines split by \n, words split on whitespace
    lines = text.splitlines()
    words = [w for w in text.split()]
    stats = {"path": str(p), "lines": len(lines), "words": len(words), "chars": len(text)}
    return {"id": req_id, "result": stats}


def dispatch(obj):
    if not isinstance(obj, dict):
        return {"id": None, "error": {"code": 400, "message": "request must be a JSON object"}}
    req_id = obj.get("id")
    method = obj.get("method")
    if method == "tools/list":
        return list_tools(req_id)
    if method == "tools/call":
        params = obj.get("params", {})
        name = params.get("name")
        args = params.get("args", {})
        if name != "textstats":
            return {"id": req_id, "error": {"code": 400, "message": f"unknown tool: {name}"}}
        return call_textstats(req_id, args)
    return {"id": req_id, "error": {"code": 400, "message": f"unknown method: {method}"}}


def main():
    # Process line-delimited JSON requests from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as e:
            write({"id": None, "error": {"code": 400, "message": f"invalid json: {e}"}})
            continue
        resp = dispatch(obj)
        write(resp)


if __name__ == "__main__":
    main()
