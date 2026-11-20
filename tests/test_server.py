import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1], timeout=5
        )

    def tearDown(self):
        self.connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        self.connection.request(method, path, body=body, headers=headers or {})
        response = self.connection.getresponse()
        return response.status, response.getheaders(), response.read().decode("utf-8")

    def test_home_form_and_successful_shortening(self):
        status, _, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('action="/shorten"', body)

        status, _, body = self.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "https://example.com/a"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 200)
        self.assertIn("<code>1</code>", body)
        self.assertIn("/1", body)

    def test_short_code_redirects_and_unknown_code_is_404(self):
        self.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "https://example.com/a"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        status, headers, _ = self.request("GET", "/1")
        self.assertEqual(status, 302)
        self.assertIn(("Location", "https://example.com/a"), headers)

        status, _, _ = self.request("GET", "/unknown")
        self.assertEqual(status, 404)

    def test_invalid_form_input_is_a_client_error(self):
        status, _, body = self.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "ftp://example.com"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(status, 400)
        self.assertIn("단축할 수 없습니다", body)

    def test_table_displays_chains_probe_counts_and_hash_steps(self):
        self.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "https://example.com/a"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        status, _, body = self.request("GET", "/table")
        self.assertEqual(status, 200)
        self.assertIn("연결 리스트", body)
        self.assertIn("비교 1회", body)
        self.assertIn("mod 1024", body)


if __name__ == "__main__":
    unittest.main()
