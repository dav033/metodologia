import unittest

from app.intervals import merge_intervals


class MergeIntervalsTests(unittest.TestCase):
    def test_touching_overlap_and_sorted_output(self):
        self.assertEqual(
            merge_intervals([(8, 10), (3, 5), (1, 3), (4, 7)]),
            [(1, 7), (8, 10)],
        )

    def test_empty_intervals_do_not_bridge_gaps(self):
        self.assertEqual(
            merge_intervals([(1, 2), (3, 3), (4, 5), (0, 0)]),
            [(1, 2), (4, 5)],
        )
        self.assertEqual(merge_intervals([(2, 2), (-1, -1)]), [])
        self.assertEqual(merge_intervals([]), [])

    def test_reversed_bounds_raise_even_with_empty_intervals(self):
        for intervals in (
            [(0, 0), (3, 2)],
            [(3, 2), (0, 0)],
            [(0, 10), (5, 4)],
        ):
            with self.subTest(intervals=intervals):
                with self.assertRaises(ValueError):
                    merge_intervals(iter(intervals))

    def test_negatives_duplicates_nesting_and_generator(self):
        intervals = [(-3, 0), (-5, -1), (-5, -1), (-4, -2), (0, 2)]
        self.assertEqual(merge_intervals(pair for pair in intervals), [(-5, 2)])
        self.assertEqual(merge_intervals(iter(())), [])

    def test_preserves_mutable_input_and_returns_tuples(self):
        intervals = [[5, 7], [1, 4], [4, 6], [2, 2]]
        before = [pair[:] for pair in intervals]
        result = merge_intervals(intervals)
        self.assertEqual(intervals, before)
        self.assertEqual(result, [(1, 7)])
        self.assertIsNot(result, intervals)
        self.assertIsInstance(result[0], tuple)

    def test_invalid_input_is_preserved(self):
        intervals = [[3, 2], [0, 0]]
        with self.assertRaises(ValueError):
            merge_intervals(intervals)
        self.assertEqual(intervals, [[3, 2], [0, 0]])


if __name__ == "__main__":
    unittest.main()
