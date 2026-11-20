"""Standard-library HTTP interface for the URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, unquote, urlsplit

from src.shortener import Shortener


def _render_table(shortener):
    table = shortener.url_table
    linear = shortener.table_type == "linear"
    title = "선형 탐지 해시 테이블" if linear else "분리 연결 해시 테이블"
    column = "슬롯" if linear else "버킷"
    contents_heading = "저장 내용" if linear else "연결 리스트"
    location_label = "초기 슬롯은" if linear else "버킷 인덱스는"
    parts = [
        "<!doctype html><html lang=\"ko\"><meta charset=\"utf-8\">",
        f"<title>{title}</title><h1>{title}</h1>",
        f"<p>{location_label} Horner 식 h = (31h + ord(c)) mod "
        f"{table.capacity}으로 계산합니다.</p>",
        f"<table border=\"1\"><thead><tr><th>{column}</th><th>{contents_heading}</th>"
        "<th>해시 계산 및 탐색</th></tr></thead><tbody>",
    ]
    for index, slot in enumerate(table.slots()):
        if linear:
            if slot is None:
                contents = "(비어 있음)"
                details = ""
            elif slot == "<deleted>":
                contents = "(삭제 표식)"
                details = ""
            else:
                key, value = slot
                steps = table.hash_steps(key)
                initial = steps[-1][2] if steps else 0
                path = table.probe_path(key)
                calculations = []
                previous = 0
                for _, codepoint, current in steps:
                    calculations.append(
                        f"(31×{previous} + {codepoint}) mod {table.capacity} = {current}"
                    )
                    previous = current
                details = (
                    f"<li><code>{escape(key)}</code> 시작 슬롯 {initial}; "
                    f"방문 슬롯 {' → '.join(str(cell) for cell in path)}; "
                    f"{len(path)}칸 확인; {'; '.join(calculations)}</li>"
                )
                contents = f"{escape(key)} → {escape(value)}"
            parts.append(
                f"<tr><td>{index}</td><td>{contents}</td><td><ul>{details}</ul></td></tr>"
            )
            continue

        chain = " → ".join(
            f"{escape(key)} → {escape(value)}" for key, value in slot
        )
        if not chain:
            chain = "(비어 있음)"
        details = []
        for key, value in slot:
            previous = 0
            calculations = []
            for _, codepoint, current in table.hash_steps(key):
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
    if shortener is None:
        shared_shorteners = [
            ("chaining", Shortener()),
            ("linear", Shortener(table_type="linear")),
        ]
    else:
        shared_shorteners = [(shortener.table_type, shortener)]

    def select_shortener(query):
        requested = "chaining"
        for name, value in parse_qsl(query, keep_blank_values=True):
            if name == "table":
                requested = value
                break
        for table_type, selected in shared_shorteners:
            if table_type == requested:
                return selected
        return None

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
                    "<p>해시 테이블: <a href=\"/table?table=chaining\">체이닝</a> · "
                    "<a href=\"/table?table=linear\">선형 탐지</a></p></html>",
                )
                return

            if route.path == "/table":
                selected = select_shortener(route.query)
                if selected is None:
                    self._respond(400, "<h1>table은 chaining 또는 linear여야 합니다.</h1>")
                    return
                self._respond(200, _render_table(selected))
                return

            selected = select_shortener(route.query)
            if selected is None:
                self._respond(400, "<h1>table은 chaining 또는 linear여야 합니다.</h1>")
                return
            code = unquote(route.path[1:])
            if not code or "/" in code:
                self._respond(404, "<h1>짧은 코드를 찾을 수 없습니다.</h1>")
                return
            try:
                target = selected.expand(code)
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
                code = None
                for _, selected in shared_shorteners:
                    shortened = selected.shorten(url)
                    if code is None:
                        code = shortened
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
                "<a href=\"/table?table=chaining\">체이닝 테이블</a> · "
                "<a href=\"/table?table=linear\">선형 탐지 테이블</a></p></html>",
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
