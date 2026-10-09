from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from service import subscribe, unsubscribe, list_subscribers

WEB_DIR = Path(__file__).parent / "web"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, obj):
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
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_GET(self):
        if self.path == "/api/subscribers":
            return self._send_json(200, {"subscribers": list_subscribers()})
        # static files
        target = "index.html" if self.path == "/" else self.path.lstrip("/")
        path = WEB_DIR / target
        try:
            # Basic containment check to avoid path traversal
            if not path.resolve().is_relative_to(WEB_DIR.resolve()):
                return self._send_json(404, {"error": "not found"})
        except AttributeError:
            # Python < 3.9 fallback: manual prefix check
            web = str(WEB_DIR.resolve())
            if not str(path.resolve()).startswith(web):
                return self._send_json(404, {"error": "not found"})
        if path.is_file():
            data = path.read_bytes()
            if path.suffix == ".html":
                ctype = "text/html; charset=utf-8"
            elif path.suffix == ".css":
                ctype = "text/css; charset=utf-8"
            elif path.suffix == ".js":
                ctype = "application/javascript; charset=utf-8"
            else:
                ctype = "text/plain; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        return self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/subscribe":
            body = self._read_json()
            try:
                return self._send_json(200, subscribe(body.get("name", "")))
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
        if self.path == "/api/unsubscribe":
            body = self._read_json()
            try:
                return self._send_json(200, unsubscribe(body.get("name", "")))
            except ValueError as e:
                return self._send_json(400, {"error": str(e)})
        return self._send_json(404, {"error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 8000):
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Serving http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
