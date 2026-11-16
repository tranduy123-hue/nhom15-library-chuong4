"""Integer fine calculation, expressed in the same currency units as 5,000."""


class FineCalculator:
    @staticmethod
    def calculate(days_overdue: int) -> int:
        """Charge 5,000/day; above 10 days add 20% to the entire fine."""
        if isinstance(days_overdue, bool) or not isinstance(days_overdue, int):
            raise TypeError("days_overdue must be an integer.")
        if days_overdue <= 0:
            return 0
        base = days_overdue * 5000
        return base * 120 // 100 if days_overdue > 10 else base
