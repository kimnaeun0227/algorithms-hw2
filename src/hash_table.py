"""Separate-chaining hash table with inspectable Horner hashing."""

_MISSING = object()


class HashTable:
    def __init__(self, capacity=8):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.size = 0
        self._buckets = [[] for _ in range(capacity)]

    def hash_steps(self, key):
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            codepoint = ord(character)
            value = (31 * value + codepoint) % self.capacity
            steps.append((character, codepoint, value))
        return steps

    def _index(self, key):
        steps = self.hash_steps(key)
        return steps[-1][2] if steps else 0

    @staticmethod
    def _validate_key(key):
        if not isinstance(key, str):
            raise TypeError("key must be a string")

    def search(self, key):
        index = self._index(key)
        probes = 0
        for stored_key, value in self._buckets[index]:
            probes += 1
            if stored_key == key:
                return True, value, probes
        return False, None, probes

    def get(self, key, default=_MISSING):
        found, value, _ = self.search(key)
        if found:
            return value
        if default is not _MISSING:
            return default
        raise KeyError(key)

    def set(self, key, value):
        index = self._index(key)
        bucket = self._buckets[index]
        for position, (stored_key, _) in enumerate(bucket):
            if stored_key == key:
                bucket[position] = (key, value)
                return
        bucket.append((key, value))
        self.size += 1

    def delete(self, key):
        index = self._index(key)
        bucket = self._buckets[index]
        for position, (stored_key, _) in enumerate(bucket):
            if stored_key == key:
                del bucket[position]
                self.size -= 1
                return True
        return False

    def slots(self):
        return [bucket.copy() for bucket in self._buckets]

    def __contains__(self, key):
        found, _, _ = self.search(key)
        return found
