"""Standard-library HTTP interface for the URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, unquote, urlsplit

from src.shortener import Shortener


def _render_table(shortener):
    table = shortener.url_table
    parts = [
        "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">",
        "<title>해시 테이블</title><h1>분리 연결 해시 테이블</h1>",
        "<p>버킷 인덱스는 Horner 식 h = (31h + ord(c)) mod "
        f"{table.capacity}으로 계산합니다.</p>",
        "<table border=\"1\"><thead><tr><th>버킷</th><th>연결 리스트</th>"
        "<th>해시 계산 및 탐색</th></tr></thead><tbody>",
    ]
    for index, bucket in enumerate(table.slots()):
        chain = " → ".join(
            f"{escape(key)} → {escape(value)}" for key, value in bucket
        )
        if not chain:
            chain = "(비어 있음)"
        details = []
        for key, value in bucket:
            previous = 0
            calculations = []
            for character, codepoint, current in table.hash_steps(key):
                calculations.append(
                    f"(31×{previous} + {codepoint}) mod {table.capacity} = {current}"
                )
                previous = current
            _, _, probes = table.search(key)
            details.append(
                f"<li><code>{escape(key)}</code> → <code>{escape(value)}</code>; "
                f"비교 {probes}회; {'; '.join(calculations)}</li>"
            )
        parts.append(
            f"<tr><td>{index}</td><td>{chain}</td><td><ul>{''.join(details)}</ul>"
            "</td></tr>"
        )
    parts.extend(
        [
            "</tbody></table><p><a href=\"/\">돌아가기</a></p></html>",
        ]
    )
    return "".join(parts)


def make_handler(shortener=None):
    shared_shortener = shortener if shortener is not None else Shortener()

    class ShortenerHandler(BaseHTTPRequestHandler):
        def _respond(self, status, body, content_type="text/html; charset=utf-8"):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            route = urlsplit(self.path)
            if route.path == "/":
                self._respond(
                    200,
                    "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
                    "<title>URL 단축기</title><h1>URL 단축기</h1>"
                    "<form method=\"post\" action=\"/shorten\">"
                    "<label>URL <input name=\"url\" type=\"url\" required></label>"
                    "<button type=\"submit\">단축</button></form>"
                    "<p><a href=\"/table\">해시 테이블 보기</a></p></html>",
                )
                return

            if route.path == "/table":
                self._respond(200, _render_table(shared_shortener))
                return

            code = unquote(route.path[1:])
            if not code or "/" in code:
                self._respond(404, "<h1>짧은 코드를 찾을 수 없습니다.</h1>")
                return
            try:
                target = shared_shortener.expand(code)
            except KeyError:
                self._respond(404, "<h1>짧은 코드를 찾을 수 없습니다.</h1>")
                return
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            if urlsplit(self.path).path != "/shorten":
                self._respond(404, "<h1>페이지를 찾을 수 없습니다.</h1>")
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._respond(400, "<h1>잘못된 요청입니다.</h1>")
                return
            if content_length < 0 or content_length > 16384:
                self._respond(413, "<h1>요청이 너무 큽니다.</h1>")
                return
            try:
                form_body = self.rfile.read(content_length).decode("utf-8")
            except UnicodeDecodeError:
                self._respond(400, "<h1>요청은 UTF-8이어야 합니다.</h1>")
                return
            url = None
            for name, value in parse_qsl(form_body, keep_blank_values=True):
                if name == "url":
                    url = value
                    break
            if url is None:
                self._respond(400, "<h1>URL을 입력해야 합니다.</h1>")
                return
            try:
                code = shared_shortener.shorten(url)
            except (TypeError, ValueError, OverflowError) as error:
                self._respond(400, f"<h1>URL을 단축할 수 없습니다.</h1><p>{escape(str(error))}</p>")
                return

            host = escape(self.headers.get("Host", "localhost"), quote=True)
            short_url = f"http://{host}/{code}"
            self._respond(
                200,
                "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">"
                "<title>단축 결과</title><h1>단축 결과</h1>"
                f"<p>코드: <code>{escape(code)}</code></p>"
                f"<p><a href=\"/{escape(code, quote=True)}\">{short_url}</a></p>"
                "<p><a href=\"/\">다른 URL 입력</a> · "
                "<a href=\"/table\">테이블 보기</a></p></html>",
            )

    return ShortenerHandler


def create_server(host="0.0.0.0", port=8000, shortener=None):
    return HTTPServer((host, port), make_handler(shortener))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    arguments = parser.parse_args(argv)
    server = create_server(host=arguments.host, port=arguments.port)
    print(f"Serving on http://{arguments.host}:{arguments.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
