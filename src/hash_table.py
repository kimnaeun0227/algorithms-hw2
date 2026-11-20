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


class LinearProbingHashTable(HashTable):
    """Fixed-capacity open-addressing table with tombstones for deletion."""

    def __init__(self, capacity=8):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity = capacity
        self.size = 0
        self._tombstone = object()
        self._slots = [None] * capacity

    def _search_with_path(self, key):
        index = self._index(key)
        path = []
        for offset in range(self.capacity):
            slot_index = (index + offset) % self.capacity
            path.append(slot_index)
            slot = self._slots[slot_index]
            if slot is None:
                return False, None, path
            if slot is self._tombstone:
                continue
            stored_key, value = slot
            if stored_key == key:
                return True, value, path
        return False, None, path

    def search(self, key):
        found, value, path = self._search_with_path(key)
        return found, value, len(path)

    def probe_path(self, key):
        """Return the slot indexes visited by a lookup, including its stopping slot."""
        _, _, path = self._search_with_path(key)
        return path

    def set(self, key, value):
        index = self._index(key)
        first_tombstone = None
        for offset in range(self.capacity):
            slot_index = (index + offset) % self.capacity
            slot = self._slots[slot_index]
            if slot is self._tombstone:
                if first_tombstone is None:
                    first_tombstone = slot_index
                continue
            if slot is None:
                insert_at = (
                    first_tombstone if first_tombstone is not None else slot_index
                )
                self._slots[insert_at] = (key, value)
                self.size += 1
                return
            stored_key, _ = slot
            if stored_key == key:
                self._slots[slot_index] = (key, value)
                return

        if first_tombstone is not None:
            self._slots[first_tombstone] = (key, value)
            self.size += 1
            return
        raise OverflowError("hash table is full")

    def delete(self, key):
        index = self._index(key)
        for offset in range(self.capacity):
            slot_index = (index + offset) % self.capacity
            slot = self._slots[slot_index]
            if slot is None:
                return False
            if slot is self._tombstone:
                continue
            stored_key, _ = slot
            if stored_key == key:
                self._slots[slot_index] = self._tombstone
                self.size -= 1
                return True
        return False

    def slots(self):
        return [
            "<deleted>" if slot is self._tombstone else slot
            for slot in self._slots
        ]
