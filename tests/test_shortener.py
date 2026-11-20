import unittest

from src.shortener import Shortener


class ShortenerTests(unittest.TestCase):
    def test_codes_are_sequential_and_urls_are_idempotent(self):
        first_url = "https://example.com/a"
        second_url = "http://example.org/b"

        for table_type in ("chaining", "linear"):
            with self.subTest(table_type=table_type):
                shortener = Shortener(table_type=table_type, capacity=3)
                first_code = shortener.shorten(first_url)
                self.assertEqual(first_code, "1")
                self.assertEqual(shortener.shorten(first_url), first_code)
                self.assertEqual(shortener.shorten(second_url), "2")
                self.assertEqual(shortener.expand(first_code), first_url)
                self.assertEqual(shortener.expand("2"), second_url)

    def test_invalid_urls_are_rejected(self):
        shortener = Shortener()
        for url in (
            "/relative/path",
            "ftp://example.com",
            "https:///missing-host",
            "https://example.com/has space",
            "",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_invalid_types_and_unknown_codes_are_rejected(self):
        shortener = Shortener()
        with self.assertRaises(TypeError):
            shortener.shorten(None)
        with self.assertRaises(KeyError):
            shortener.expand("unknown")

    def test_unsupported_table_type_is_rejected(self):
        with self.assertRaises(ValueError):
            Shortener(table_type="probing")

    def test_linear_shortener_reports_capacity_exhaustion(self):
        shortener = Shortener(table_type="linear", capacity=1)
        shortener.shorten("https://example.com/1")
        with self.assertRaises(OverflowError):
            shortener.shorten("https://example.com/2")


if __name__ == "__main__":
    unittest.main()
