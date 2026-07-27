import unittest

from life_velocities.quotient import StripQuotient


class QuotientTests(unittest.TestCase):
    def test_relations_and_size(self):
        quotient = StripQuotient(10, 6, 7, 3, 2)
        self.assertEqual(len(quotient.representatives()), quotient.cell_count)
        for point in ((0, 0, 0), (13, -4, 2), (-9, 8, -1)):
            t, x, y = point
            key = quotient.key(*point)
            self.assertEqual(key, quotient.key(t + 10, x + 6, y))
            self.assertEqual(key, quotient.key(t - 2, x + 7, y))
            self.assertEqual(key, quotient.key(t, x, y + 3))

    def test_rejects_degenerate_quotient(self):
        with self.assertRaises(ValueError):
            StripQuotient(2, 2, 2, 1, -2)


if __name__ == "__main__":
    unittest.main()
