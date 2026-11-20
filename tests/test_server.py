import http.client
import threading
import unittest
from urllib.parse import urlencode

from src.server import create_server
from src.shortener import Shortener


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
        self.assertIn("/table?table=linear", body)

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

    def test_table_renders_linked_url_nodes_with_expandable_hash_steps(self):
        server = create_server(
            host="127.0.0.1", port=0, shortener=Shortener(capacity=1)
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            for url in ("https://example.com/a", "https://example.com/b"):
                connection.request(
                    "POST",
                    "/shorten",
                    body=urlencode({"url": url}),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()

            connection.request("GET", "/table")
            response = connection.getresponse()
            body = response.read().decode("utf-8")

            self.assertEqual(response.status, 200)
            self.assertIn("https://example.com/a", body)
            self.assertIn("https://example.com/b", body)
            self.assertIn('href="/1"', body)
            self.assertIn('href="/2"', body)
            self.assertIn("<details>", body)
            self.assertIn("Horner", body)
            self.assertIn("→", body)
            self.assertIn("비교 2회", body)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_linear_table_shows_visited_slots_and_hash_steps(self):
        self.request(
            "POST",
            "/shorten",
            body=urlencode({"url": "https://example.com/a"}),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        status, _, body = self.request("GET", "/table?table=linear")

        self.assertEqual(status, 200)
        self.assertIn("선형 탐지", body)
        self.assertIn("초기 슬롯은 Horner", body)
        self.assertIn("방문 슬롯", body)
        self.assertIn("시작 슬롯", body)
        self.assertIn("mod 1024", body)

    def test_unknown_table_selection_is_rejected(self):
        status, _, _ = self.request("GET", "/table?table=unknown")
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
