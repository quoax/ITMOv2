#!/usr/bin/env python3
"""Minimal E2E checks for pagination/sort contract.
Standard library only. Starts HTTP server in a background thread,
performs a sequence of API calls via urllib, and writes results to results_e2e.md
"""
from __future__ import annotations
import json
import time
import threading
from urllib import request, parse, error
from http_server import create_server
from service import subscribers, subscribe


def http_get(url: str):
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def run():
    # Start server on ephemeral port
    server = create_server(port=0)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    host, port = server.server_address
    base = f"http://{host}:{port}"

    # Prepare data
    subscribers.clear()
    for i in range(1, 7):
        subscribe(f"user{i}@example.com")

    # 1) Success basic page asc
    status1, body1 = http_get(base + "/api/v1/subscribers?offset=0&limit=2&sort=asc")
    # 2) Next page
    status2, body2 = http_get(base + "/api/v1/subscribers?offset=2&limit=2&sort=asc")
    # 3) Desc order
    status3, body3 = http_get(base + "/api/v1/subscribers?offset=0&limit=3&sort=desc")

    # 4) Validation errors
    def get_err(q):
        try:
            return http_get(base + "/api/v1/subscribers?" + q)
        except error.HTTPError as e:
            payload = json.loads(e.read().decode("utf-8"))
            return e.code, payload

    st4, err4 = get_err("limit=1000")
    st5, err5 = get_err("offset=-1")
    st6, err6 = get_err("sort=bad")

    # 5) Edge: offset beyond total
    st7, body7 = http_get(base + "/api/v1/subscribers?offset=100&limit=10&sort=asc")
    # 6) Internal error (500) via test hook
    st8, err8 = get_err("__test_internal=1")

    # Stop server
    server.shutdown()
    server.server_close()

    # Compose results
    lines = []
    lines.append("# E2E Results: Pagination & Sort\n")
    lines.append("## Success Scenarios\n")
    lines.append(f"- Page1 status={status1}, items={len(body1['items'])}, total={body1['total']}")
    lines.append(f"- Page2 status={status2}, items={len(body2['items'])}, total={body2['total']}")
    lines.append(f"- Desc status={status3}, first={body3['items'][0]['created_at']}.., total={body3['total']}")
    lines.append("\n## Validation Errors\n")
    lines.append(f"- limit>100 => {st4}, code={err4.get('error',{}).get('code')} details={err4.get('error',{}).get('details')}")
    lines.append(f"- offset<0 => {st5}, code={err5.get('error',{}).get('code')} details={err5.get('error',{}).get('details')}")
    lines.append(f"- sort invalid => {st6}, code={err6.get('error',{}).get('code')} details={err6.get('error',{}).get('details')}")
    lines.append("\n## Edge Conditions\n")
    lines.append(f"- offset beyond total => {st7}, items={len(body7['items'])}, total={body7['total']}")
    lines.append("\n## Internal Error\n")
    lines.append(f"- simulated internal error => {st8}, code={err8.get('error',{}).get('code')}")

    content = "\n".join(lines) + "\n"
    with open("results_e2e.md", "w", encoding="utf-8") as f:
        f.write(content)
    with open("result.md", "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    run()
