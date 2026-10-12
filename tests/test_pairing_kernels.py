"""Count actual pinned-reference kernel calls, including exceptional branches."""
from collections import Counter
import unittest
from py_ecc.optimized_bls12_381 import G1, G2, add, double, neg, twist
from py_ecc.optimized_bls12_381.optimized_pairing import linefunc, cast_point_to_fq12


class CountedField:
    counts = Counter()

    def __init__(self, value):
        self.value = value

    def zero(self):
        return CountedField(self.value.zero())

    def one(self):
        return CountedField(self.value.one())

    def __mul__(self, other):
        self.counts['products'] += 1
        return CountedField(self.value * (other.value if isinstance(other, CountedField) else other))

    __rmul__ = __mul__

    def __sub__(self, other):
        self.counts['subtractions'] += 1
        return CountedField(self.value - (other.value if isinstance(other, CountedField) else other))

    def __eq__(self, other):
        self.counts['comparisons'] += 1
        return self.value == (other.value if isinstance(other, CountedField) else other)


def counted(point):
    return tuple(CountedField(v) for v in point)


class PairingKernels(unittest.TestCase):
    def test_reference_branches_fit_the_published_field_call_budgets(self):
        # Execute organizer-pinned library functions, never candidate source.
        # This audits field-call counts; the candidate separately lowers those
        # calls to word-RAM primitives and charges transfers/control.
        q, q2 = counted(G2), counted(double(G2))
        tq, tq2, tminus = map(counted, (twist(G2), twist(double(G2)), twist(neg(G2))))
        p = counted(cast_point_to_fq12(G1))
        cases = [('point double', lambda: double(q), 17, 3),
                 ('point add', lambda: add(q, q2), 15, 6),
                 ('point add doubling', lambda: add(q, q), 21, 3),
                 ('line tangent', lambda: linefunc(tq, tq, p), 16, 5),
                 ('line ordinary', lambda: linefunc(tq, tq2, p), 12, 5),
                 ('line vertical', lambda: linefunc(tq, tminus, p), 7, 3)]
        for name, call, products, subtractions in cases:
            with self.subTest(kernel=name):
                CountedField.counts.clear()
                call()
                self.assertEqual(CountedField.counts['products'], products)
                self.assertEqual(CountedField.counts['subtractions'], subtractions)
                self.assertLessEqual(CountedField.counts['comparisons'], 4)


if __name__ == '__main__':
    unittest.main()
