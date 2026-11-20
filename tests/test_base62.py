import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trip_values(self):
        for value in (0, 1, 61, 62, 3843, 10**30):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_zero_is_encoded_as_zero(self):
        self.assertEqual(encode(0), "0")

    def test_alphabet_boundaries(self):
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_negative_value_is_rejected(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_wrong_input_types_are_rejected(self):
        with self.assertRaises(TypeError):
            encode(True)
        with self.assertRaises(TypeError):
            decode(1)

    def test_empty_or_invalid_encoded_value_is_rejected(self):
        for encoded in ("", "a+", "가"):
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):
                    decode(encoded)


if __name__ == "__main__":
    unittest.main()
