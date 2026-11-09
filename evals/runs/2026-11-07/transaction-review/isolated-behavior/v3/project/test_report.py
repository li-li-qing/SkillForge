import unittest
from report import total

class TotalTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(total([{"count": 2}, {"count": 3}]), 5)
    def test_empty(self):
        self.assertEqual(total([]), 0)
    def test_csv_counts(self):
        self.assertEqual(total([{"count": "2"}, {"count": "3"}]), 5)

    def test_mixed_counts(self):
        self.assertEqual(total([{"count": 2}, {"count": "3"}]), 5)

    def test_signed_and_padded_counts(self):
        for value, expected in [("  +002 \t", 2), ("-3", -3), ("0", 0)]:
            with self.subTest(value=value):
                self.assertEqual(total([{"count": value}]), expected)

    def test_integer_behavior(self):
        self.assertEqual(total([{"count": -3}, {"count": 0}, {"count": 10**80}]), 10**80 - 3)
        self.assertEqual(total([{"count": str(10**80)}]), 10**80)

    def test_invalid_strings_raise(self):
        for value in ["", " ", "bad", "2.5", "2.0", "1e3", "0x10", "1_000", "+", "1 2"]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "count"):
                    total([{"count": 1}, {"count": value}])

    def test_invalid_types_raise(self):
        for value in [None, 2.5, 2.0, [], {}]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "count"):
                    total([{"count": value}])

    def test_missing_count_raises(self):
        with self.assertRaises(KeyError):
            total([{}])
