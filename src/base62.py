"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE = len(ALPHABET)


def encode(value: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an integer")
    if value < 0:
        raise ValueError("value must be non-negative")
    if value == 0:
        return "0"

    digits = []
    while value:
        value, remainder = divmod(value, _BASE)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


def decode(encoded: str) -> int:
    """Decode a non-empty base62 string into a non-negative integer."""
    if not isinstance(encoded, str):
        raise TypeError("encoded value must be a string")
    if not encoded:
        raise ValueError("encoded value must not be empty")

    value = 0
    for character in encoded:
        try:
            digit = ALPHABET.index(character)
        except ValueError as error:
            raise ValueError(f"invalid base62 character: {character!r}") from error
        value = value * _BASE + digit
    return value
