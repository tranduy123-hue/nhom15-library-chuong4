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


class RoleCFineEnhancementTests(unittest.TestCase):
    """UT2 (KAN-26): Bổ sung unit test tính tiền phạt quá hạn bởi Lê Quân Bảo."""

    def test_fifteen_days_overdue_fine_with_surcharge(self):
        # 1. Arrange: quá hạn 15 ngày (> 10 ngày áp dụng phụ phí 20%)
        days_overdue = 15
        expected = int(15 * 5000 * 1.2)  # 90.000 đ
        # 2. Act
        result = FineCalculator.calculate(days_overdue)
        # 3. Assert
        self.assertEqual(result, expected)
        self.assertEqual(result, 90000)

    def test_thirty_days_overdue_fine_with_surcharge(self):
        # 1. Arrange: quá hạn 30 ngày
        days_overdue = 30
        expected = int(30 * 5000 * 1.2)  # 180.000 đ
        # 2. Act
        result = FineCalculator.calculate(days_overdue)
        # 3. Assert
        self.assertEqual(result, expected)
        self.assertEqual(result, 180000)

