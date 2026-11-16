"""Simulated role C: fine calculation; role labels do not claim separate humans."""
import unittest

from library import FineCalculator


class RoleCFineTests(unittest.TestCase):
    def testNoFine(self):
        # Arrange
        days_overdue = 0
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 0)

    def testNormalFine(self):
        # Arrange
        days_overdue = 5
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 25000)

    def testHeavyFine(self):
        # Arrange
        days_overdue = 11
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 66000)
        self.assertIs(type(result), int)

    def test_negative_boundary_has_no_fine(self):
        # Arrange
        days_overdue = -1
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 0)

    def test_ten_day_boundary_has_no_surcharge(self):
        # Arrange
        days_overdue = 10
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 50000)

    def test_large_fine_stays_exact(self):
        # Arrange
        days_overdue = 10 ** 20 + 1
        # Act
        result = FineCalculator.calculate(days_overdue)
        # Assert
        self.assertEqual(result, 600000000000000000006000)
        self.assertIs(type(result), int)

    def test_non_integer_days_are_rejected(self):
        # Arrange
        invalids = (True, 1.5, "5", None)
        # Act / Assert
        for days in invalids:
            with self.subTest(days=days), self.assertRaises(TypeError):
                FineCalculator.calculate(days)
