import json
import threading
import unittest
from urllib import request, error

from http_server import create_server
from service import subscribers, subscribe


class HttpContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        subscribers.clear()
        for i in range(5):
            subscribe(f"u{i}@ex.com")

    def _get(self, path):
        req = request.Request(self.base + path, method="GET")
        with request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def _get_err(self, path):
        try:
            return self._get(path)
        except error.HTTPError as e:
            payload = json.loads(e.read().decode("utf-8"))
            return e.code, payload

    def test_format_ok(self):
        st, body = self._get("/api/v1/subscribers?offset=0&limit=2&sort=asc")
        self.assertEqual(st, 200)
        self.assertIsInstance(body.get("items"), list)
        self.assertIsInstance(body.get("total"), int)
        self.assertEqual(len(body), 2)  # exactly items + total

    def test_validation_errors(self):
        st, err = self._get_err("/api/v1/subscribers?limit=1000")
        self.assertEqual(st, 400)
        self.assertEqual(err.get("error", {}).get("code"), "VALIDATION_ERROR")
        self.assertIn("limit", err.get("error", {}).get("details", {}))

        st, err = self._get_err("/api/v1/subscribers?offset=-1")
        self.assertEqual(st, 400)
        self.assertIn("offset", err.get("error", {}).get("details", {}))

        st, err = self._get_err("/api/v1/subscribers?sort=bad")
        self.assertEqual(st, 400)
        self.assertIn("sort", err.get("error", {}).get("details", {}))

    def test_internal_error(self):
        st, err = self._get_err("/api/v1/subscribers?__test_internal=1")
        self.assertEqual(st, 500)
        self.assertEqual(err.get("error", {}).get("code"), "INTERNAL_ERROR")


if __name__ == "__main__":
    unittest.main()
