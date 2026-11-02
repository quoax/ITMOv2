from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from service import subscribe, unsubscribe, list_subscribers, list_records_raw

WEB_DIR = Path(__file__).parent / "web"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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
        # Parse path and query
        parsed = urlparse(self.path)
        if parsed.path == "/api/subscribers":
            # legacy endpoint for compatibility
            return self._send_json(200, {"subscribers": list_subscribers()})
        if parsed.path == "/api/v1/subscribers" or parsed.path == "/api/v1/subscribers/":
            try:
                # REST list with pagination and sort
                qs = parse_qs(parsed.query)
                # test hook to simulate internal error
                if qs.get("__test_internal", ["0"])[0] == "1":
                    raise RuntimeError("simulated internal error")

                def get_int(name, default):
                    try:
                        if name not in qs:
                            return default
                        return int(qs.get(name, [default])[0])
                    except Exception:
                        # Force invalid to 400 later by returning sentinel
                        return None
                def get_str(name, default):
                    val = qs.get(name, [default])[0]
                    return val

                offset = get_int("offset", 0)
                limit = get_int("limit", 20)
                sort = get_str("sort", "asc")

                details = {}
                if offset is None or offset < 0:
                    details["offset"] = "must be >= 0"
                if limit is None or limit < 1 or limit > 100:
                    details["limit"] = "must be between 1 and 100"
                if sort not in ("asc", "desc"):
                    details["sort"] = "must be one of asc, desc"
                if details:
                    return self._send_json(400, {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid query parameters",
                            "details": details,
                        }
                    })

                # Build list and apply sort, total, slice
                records = list_records_raw()
                total = len(records)
                # sort by created_ts asc/desc, tie-break by id asc
                reverse = (sort == "desc")
                records.sort(key=lambda r: (r.get("created_ts", 0.0), r.get("id", "")))
                if reverse:
                    # reverse while preserving tie-breaker semantics
                    records.reverse()
                page = records[offset: offset + limit]
                # map to public fields
                items = [{"id": r["id"], "email": r["email"], "created_at": r["created_at"]} for r in page]
                return self._send_json(200, {"items": items, "total": total})
            except Exception:
                return self._send_json(500, {
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "unexpected server error",
                        "details": {},
                    }
                })
        # API 404 envelope for unknown /api/v1/* paths
        if parsed.path.startswith("/api/v1/"):
            return self._send_json(404, {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "not found",
                    "details": {},
                }
            })
        # static files
        target = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
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

def create_server(host: str = "127.0.0.1", port: int = 8000):
    """Create a server instance for test usage without blocking."""
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    serve()
