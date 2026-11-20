import unittest

from src.hash_table import HashTable, LinearProbingHashTable


class HashTableTests(unittest.TestCase):
    def test_capacity_must_be_a_positive_integer(self):
        for capacity in (0, -1, 2.5, True):
            with self.subTest(capacity=capacity):
                with self.assertRaises(ValueError):
                    HashTable(capacity)

    def test_collisions_updates_and_search_probes(self):
        table = HashTable(capacity=2)
        table.set("a", 1)
        table.set("c", 2)

        self.assertEqual(table.search("a"), (True, 1, 1))
        self.assertEqual(table.search("c"), (True, 2, 2))
        self.assertEqual(table.search("e"), (False, None, 2))
        table.set("a", 3)
        self.assertEqual(table.get("a"), 3)
        self.assertEqual(table.size, 2)

    def test_missing_default_delete_and_reinsert(self):
        table = HashTable(capacity=3)
        self.assertEqual(table.get("missing", "fallback"), "fallback")
        with self.assertRaises(KeyError):
            table.get("missing")
        table.set("key", "value")
        self.assertTrue(table.delete("key"))
        self.assertFalse(table.delete("key"))
        self.assertEqual(table.search("key"), (False, None, 0))
        table.set("key", "again")
        self.assertEqual(table.get("key"), "again")

    def test_slots_and_horner_hash_steps_are_inspectable(self):
        table = HashTable(capacity=5)
        table.set("ab", "value")
        steps = table.hash_steps("ab")

        self.assertEqual(steps, [("a", ord("a"), 2), ("b", ord("b"), 0)])
        self.assertEqual(table.slots()[0], [("ab", "value")])

    def test_keys_must_be_strings(self):
        table = HashTable()
        with self.assertRaises(TypeError):
            table.set(1, "value")
        with self.assertRaises(TypeError):
            table.search(None)


class LinearProbingHashTableTests(unittest.TestCase):
    def test_wraps_from_last_slot_and_visits_until_empty_slot(self):
        table = LinearProbingHashTable(capacity=4)
        table.set("c", 1)
        table.set("g", 2)

        self.assertEqual(table.slots()[3], ("c", 1))
        self.assertEqual(table.slots()[0], ("g", 2))
        self.assertEqual(table.search("g"), (True, 2, 2))
        self.assertEqual(table.probe_path("k"), [3, 0, 1])

    def test_tombstone_preserves_probe_chain_and_can_be_reused(self):
        table = LinearProbingHashTable(capacity=4)
        table.set("c", 1)
        table.set("g", 2)

        self.assertTrue(table.delete("c"))
        self.assertEqual(table.slots()[3], "<deleted>")
        self.assertEqual(table.get("g"), 2)
        self.assertEqual(table.probe_path("g"), [3, 0])
        table.set("k", 3)
        self.assertEqual(table.slots()[3], ("k", 3))
        self.assertEqual(table.size, 2)

    def test_full_table_rejects_new_keys_but_updates_existing_keys(self):
        table = LinearProbingHashTable(capacity=2)
        table.set("a", 1)
        table.set("b", 2)

        with self.assertRaises(OverflowError):
            table.set("c", 3)
        table.set("a", 4)
        self.assertEqual(table.get("a"), 4)
        self.assertEqual(table.search("c"), (False, None, 2))
        self.assertEqual(table.size, 2)

    def test_common_get_delete_and_membership_interface(self):
        table = LinearProbingHashTable(capacity=3)
        self.assertEqual(table.search("missing"), (False, None, 1))
        table.set("key", "value")
        self.assertIn("key", table)
        self.assertEqual(table.get("key"), "value")
        self.assertTrue(table.delete("key"))
        self.assertNotIn("key", table)
        self.assertEqual(table.get("missing", "fallback"), "fallback")


if __name__ == "__main__":
    unittest.main()
