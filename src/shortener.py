"""URL shortener backed by the project's separate-chaining hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashTable, LinearProbingHashTable


class Shortener:
    def __init__(self, table_type="chaining", capacity=1024):
        if table_type == "chaining":
            table_class = HashTable
        elif table_type == "linear":
            table_class = LinearProbingHashTable
        else:
            raise ValueError("table_type must be 'chaining' or 'linear'")
        self.table_type = table_type
        self._urls = table_class(capacity)
        self._codes = table_class(capacity)
        self._next_id = 1

    @property
    def url_table(self):
        return self._urls

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if not url or any(character.isspace() for character in url):
            raise ValueError("url must be an absolute HTTP(S) URL")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url must be a valid absolute HTTP(S) URL") from error
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not hostname:
            raise ValueError("url must be an absolute HTTP(S) URL")

    def shorten(self, url):
        self._validate_url(url)
        found, code, _ = self._urls.search(url)
        if found:
            return code

        code = encode(self._next_id)
        self._urls.set(url, code)
        self._codes.set(code, url)
        self._next_id += 1
        return code

    def expand(self, code):
        return self._codes.get(code)
