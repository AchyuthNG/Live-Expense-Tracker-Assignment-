"""Unit tests for the pure anomaly-detection rule functions.

No mocking required — these functions take plain numbers/lists."""
import pytest
from app.anomaly import rules


# ---------------------------------------------------------------------------
# Z-score rule
# ---------------------------------------------------------------------------

class TestCheckCategoryZscore:
    def test_no_anomaly_when_within_range(self):
        history = [100, 110, 90, 105, 95]
        # 110 gives z ≈ 1.41 < 2.0 threshold -> no flag.
        assert rules.check_category_zscore(110, history) is None

    def test_anomaly_when_way_above_mean(self):
        history = [100, 110, 90, 105, 95]
        result = rules.check_category_zscore(500, history)
        assert result is not None
        assert result.rule_triggered == "z_score"
        assert "x category average" in result.reason

    def test_skips_when_insufficient_history(self):
        history = [100, 110]
        assert rules.check_category_zscore(500, history) is None

    def test_identical_history_flags_any_higher_amount(self):
        history = [500, 500, 500, 500, 500]
        result = rules.check_category_zscore(1000, history)
        assert result is not None
        assert result.severity == "high"

    def test_no_flag_when_amount_equals_mean_with_stdev(self):
        history = [100, 110, 90, 105, 95]
        import statistics
        mean = statistics.fmean(history)
        assert rules.check_category_zscore(mean, history) is None


# ---------------------------------------------------------------------------
# Hard-cap rule
# ---------------------------------------------------------------------------

class TestCheckHardCap:
    @pytest.mark.parametrize("category,amount,expected", [
        ("groceries", 4000, None),
        ("groceries", 6000, True),
        ("food", 1500, None),
        ("food", 3000, True),
        ("travel", 14000, None),
        ("travel", 16000, True),
        ("misc", 2500, None),
        ("misc", 3500, True),
    ])
    def test_caps(self, category, amount, expected):
        result = rules.check_hard_cap(amount, category)
        if expected is None:
            assert result is None
        else:
            assert result is not None
            assert result.rule_triggered == "hard_cap"

    def test_severity_high_when_double_cap(self):
        result = rules.check_hard_cap(11_000, "groceries")
        assert result is not None
        assert result.severity == "high"


# ---------------------------------------------------------------------------
# Rent / loan deviation rules
# ---------------------------------------------------------------------------

class TestCheckRentDeviation:
    def test_flags_upward_jump(self):
        result = rules.check_rent_deviation(12000, last_rent=10000)
        assert result is not None
        assert result.rule_triggered == "rent_mismatch"
        assert "up" in result.reason

    def test_no_flag_within_tolerance(self):
        assert rules.check_rent_deviation(10500, last_rent=10000) is None

    def test_no_flag_when_no_history(self):
        assert rules.check_rent_deviation(12000, last_rent=None) is None


class TestCheckLoanDeviation:
    def test_flags_downward_change(self):
        # 4400 vs 5000 = 12% deviation, above the 10% threshold.
        result = rules.check_loan_deviation(4400, last_loan=5000)
        assert result is not None
        assert "down" in result.reason

    def test_no_flag_within_tolerance(self):
        assert rules.check_loan_deviation(5200, last_loan=5000) is None


# ---------------------------------------------------------------------------
# Daily spike rule
# ---------------------------------------------------------------------------

class TestCheckDailySpike:
    def test_flags_when_over_3x(self):
        result = rules.check_daily_spike(9000, avg_daily=2000)
        assert result is not None
        assert result.rule_triggered == "daily_spike"

    def test_no_flag_when_within_range(self):
        assert rules.check_daily_spike(5000, avg_daily=2000) is None

    def test_no_flag_when_avg_zero(self):
        assert rules.check_daily_spike(9000, avg_daily=0) is None

    def test_severity_high_when_5x(self):
        result = rules.check_daily_spike(10000, avg_daily=2000)
        assert result.severity == "high"


# ---------------------------------------------------------------------------
# Frequency rule
# ---------------------------------------------------------------------------

class TestCheckFrequency:
    def test_flags_at_threshold(self):
        result = rules.check_frequency(3)
        assert result is not None
        assert result.rule_triggered == "frequency"
        assert result.severity == "low"

    def test_no_flag_below_threshold(self):
        assert rules.check_frequency(2) is None