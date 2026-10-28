---
name: notify-mini-frontend
description: Use ONLY when building or evolving the minimal web UI and HTTP API for practices/practice_03/lab/demo (Notify Mini). Trigger on keywords/files: http_server.py, web/index.html, web/script.js, web/style.css, BaseHTTPRequestHandler, fetch, make serve. Standard library only.
---

# Notify Mini Frontend Skill

Purpose
- Provide a repeatable, opinionated workflow to design and build a minimal browser UI and an HTTP API layer on top of `service.py` in `practices/practice_03/lab/demo`.
- Enforce constraints: Python 3.10+, standard library only, minimal changes.

When to Use
- The user asks to create or adjust a frontend for demo/Notify Mini.
- The plan references files: `http_server.py`, `web/index.html`, `web/script.js`, `web/style.css`.
- The task mentions Feature A (UI+API) or Feature B (persistence and UX).

Guardrails
- Do not add external dependencies (no Flask, no npm). Only `http.server`, `urllib`, `json`.
- Keep edits local to `practices/practice_03/lab/demo` unless explicitly requested.
- Prefer smallest correct changes; reuse functions from `service.py`.

Outputs
- HTTP server: `http_server.py` using `BaseHTTPRequestHandler`/`ThreadingHTTPServer`.
- Static UI: `web/index.html`, `web/style.css`, `web/script.js`.
- Makefile target: `serve` for local run.
- Tests: extend `test_service.py` minimally when backend surface changes.

API Contract (JSON)
- `GET /api/subscribers` → `{ "subscribers": ["Ann", ...] }`
- `POST /api/subscribe` body `{ "name": "Ann" }` → `{ "subscribed": true }` (400 on empty)
- `POST /api/unsubscribe` body `{ "name": "Ann" }` → `{ "unsubscribed": true|false }`
- Static: `GET /` serves `web/index.html`; `GET /style.css`, `GET /script.js` serve static assets.

Backend Integration
- Implement/ensure:
  - `normalize_name(name)`: trim whitespace (optionally casefold if requested).
  - `subscribe(name)`, `unsubscribe(name)` return small JSON payloads.
  - `list_subscribers()` returns a stable sorted list for UI.

HTTP Server Template
```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from service import subscribe, unsubscribe, list_subscribers

WEB_DIR = Path(__file__).parent / "web"

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except Exception:
            return {}

    def do_GET(self):
        if self.path == "/api/subscribers":
            return self._send_json(200, {"subscribers": list_subscribers()})
        target = "index.html" if self.path == "/" else self.path.lstrip("/")
        path = WEB_DIR / target
        if path.is_file() and str(path.resolve()).startswith(str(WEB_DIR.resolve())):
            data = path.read_bytes()
            if path.suffix == ".html": ctype = "text/html; charset=utf-8"
            elif path.suffix == ".css": ctype = "text/css; charset=utf-8"
            elif path.suffix == ".js": ctype = "application/javascript; charset=utf-8"
            else: ctype = "text/plain; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            return self.wfile.write(data)
        return self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/subscribe":
            body = self._read_json()
            try: return self._send_json(200, subscribe(body.get("name", "")))
            except ValueError as e: return self._send_json(400, {"error": str(e)})
        if self.path == "/api/unsubscribe":
            body = self._read_json()
            try: return self._send_json(200, unsubscribe(body.get("name", "")))
            except ValueError as e: return self._send_json(400, {"error": str(e)})
        return self._send_json(404, {"error": "not found"})

def serve(host="127.0.0.1", port=8000):
    with ThreadingHTTPServer((host, port), Handler) as httpd:
        print(f"Serving http://{host}:{port}")
        httpd.serve_forever()
```

Frontend Template
```html
<!doctype html>
<html lang="ru">
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Notify Mini</title>
  <link rel="stylesheet" href="/style.css" />
  <body>
    <main>
      <h1>Управление подписками</h1>
      <form id="add-form"><input id="name" placeholder="Имя" /><button>Добавить</button><span id="status"></span></form>
      <input id="filter" placeholder="Фильтр" />
      <ul id="list"></ul>
    </main>
    <script src="/script.js"></script>
  </body>
  </html>
```

```js
async function api(path, body) {
  const res = await fetch(path, { method: body?"POST":"GET", headers: body?{"Content-Type":"application/json"}:{}, body: body?JSON.stringify(body):undefined });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Request failed");
  return json;
}
async function refresh() {
  const data = await api("/api/subscribers");
  const f = document.querySelector("#filter").value.toLowerCase();
  const list = document.querySelector("#list"); list.innerHTML = "";
  for (const name of data.subscribers) {
    if (f && !name.toLowerCase().includes(f)) continue;
    const li = document.createElement("li"); li.textContent = name;
    const btn = document.createElement("button"); btn.textContent = "Удалить";
    btn.onclick = async () => { await api("/api/unsubscribe", { name }); await refresh(); };
    li.appendChild(btn); list.appendChild(li);
  }
}
document.querySelector("#add-form").onsubmit = async (e) => { e.preventDefault(); const name = document.querySelector("#name").value; const status = document.querySelector("#status"); try { await api("/api/subscribe", { name }); status.textContent = "Добавлено"; } catch (err) { status.textContent = err.message; } finally { await refresh(); } };
document.querySelector("#filter").oninput = ((fn,ms)=>{ let t; return ()=>{ clearTimeout(t); t=setTimeout(fn,ms); };})(refresh,200);
refresh();
```

Checklist (Feature A)
- Update backend: `normalize_name`, `unsubscribe`, `list_subscribers`.
- Add server and UI files.
- Makefile `serve` target.
- Tests pass (`make -s -C practices/practice_03/lab test`).

Checklist (Feature B) — optional
- `save_state()` / `load_state()` in `service.py`.
- UI: status messages, filter input (already present), import/export routes.
- Add tests for persistence.

Acceptance
- Add and remove names via UI; filter works.
- HTTP API returns expected payloads and status codes.

How to Run
- From `practices/practice_03/lab/demo`: `make serve` then open `http://127.0.0.1:8000/`.
- Tests: `make -s -C practices/practice_03/lab test`.
