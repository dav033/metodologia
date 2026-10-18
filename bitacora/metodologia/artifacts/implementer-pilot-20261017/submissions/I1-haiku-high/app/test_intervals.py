import unittest

from app.intervals import merge_intervals


class MergeIntervalsTest(unittest.TestCase):
    def test_empty_input_returns_empty_list(self):
        self.assertEqual(merge_intervals([]), [])

    def test_overlapping_intervals_merge(self):
        self.assertEqual(merge_intervals([(3, 5), (1, 4)]), [(1, 5)])

    def test_touching_intervals_merge(self):
        self.assertEqual(merge_intervals([(1, 3), (3, 5)]), [(1, 5)])

    def test_disjoint_intervals_stay_separate_and_sorted(self):
        self.assertEqual(merge_intervals([(7, 9), (1, 2)]), [(1, 2), (7, 9)])

    def test_nested_intervals_collapse_to_outer(self):
        self.assertEqual(merge_intervals([(1, 10), (2, 3), (4, 5)]), [(1, 10)])

    def test_duplicates_collapse(self):
        self.assertEqual(merge_intervals([(1, 2), (1, 2), (1, 2)]), [(1, 2)])

    def test_empty_intervals_are_dropped(self):
        self.assertEqual(merge_intervals([(2, 2), (5, 5)]), [])
        self.assertEqual(merge_intervals([(2, 2), (1, 3)]), [(1, 3)])

    def test_negative_coordinates(self):
        self.assertEqual(
            merge_intervals([(-3, -1), (-2, 0), (5, 6)]), [(-3, 0), (5, 6)]
        )

    def test_generator_input(self):
        gen = ((s, e) for s, e in [(4, 6), (0, 2), (2, 4)])
        self.assertEqual(merge_intervals(gen), [(0, 6)])

    def test_input_is_not_mutated(self):
        data = [(3, 5), (1, 4)]
        merge_intervals(data)
        self.assertEqual(data, [(3, 5), (1, 4)])

    def test_returns_new_list(self):
        data = [(1, 2)]
        result = merge_intervals(data)
        self.assertIsNot(result, data)
        self.assertIsInstance(result[0], tuple)

    def test_reversed_bounds_raise(self):
        with self.assertRaises(ValueError):
            merge_intervals([(5, 1)])

    def test_reversed_bounds_raise_even_with_empty_intervals(self):
        with self.assertRaises(ValueError):
            merge_intervals([(2, 2), (5, 1)])

    def test_reversed_bounds_raise_from_generator(self):
        with self.assertRaises(ValueError):
            merge_intervals(iter([(1, 2), (9, 3)]))


if __name__ == "__main__":
    unittest.main()
