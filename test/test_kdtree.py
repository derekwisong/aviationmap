import unittest
from ledvfrmap.containers import KDTree


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        pass

    def test_nearest_point_tuples(self):
        points = [(7, 2), (5, 4), (9, 6), (4, 7), (8, 1), (2, 3)]
        tree = KDTree.from_points(points)
        _, nearest = tree.nearest((7, 3))
        expected = (7, 2)
        self.assertEqual(expected, nearest)

    def test_nearest_point_class(self):
        class Datum:
            def __init__(self, point):
                self.point = point

        points = [Datum(x) for x in [(7, 2), (5, 4), (9, 6), (4, 7), (8, 1), (2, 3)]]
        tree = KDTree.from_points(points, key=lambda x: x.point)
        _, nearest = tree.nearest((7, 3))
        expected = (7, 2)
        self.assertEqual(expected, nearest.point)


if __name__ == '__main__':
    unittest.main()
