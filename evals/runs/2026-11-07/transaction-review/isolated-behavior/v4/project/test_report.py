import unittest
from report import total

class TotalTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(total([{"count": 2}, {"count": 3}]), 5)
    def test_empty(self):
        self.assertEqual(total([]), 0)
    def test_csv_counts(self):
        self.assertEqual(total([{"count": "2"}, {"count": "3"}]), 5)

    def test_signed_and_padded_decimal_counts(self):
        self.assertEqual(total([{"count": " +002 "}, {"count": "-3"}, {"count": "0"}]), -1)

    def test_mixed_counts_and_large_integer(self):
        large = 10 ** 100
        self.assertEqual(total([{"count": large}, {"count": str(large)}, {"count": -2}]), 2 * large - 2)

    def test_invalid_strings_raise(self):
        for value in ("", " ", "1.5", "1e3", "0x10", "1_000", "abc", "+", "1 2"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "count"):
                    total([{"count": 1}, {"count": value}])

    def test_invalid_types_raise(self):
        for value in (None, True, False, 2.0, [], {}):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "count"):
                    total([{"count": value}])

    def test_missing_count_raises(self):
        with self.assertRaises(KeyError):
            total([{}])
