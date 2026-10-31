import pytest
from backend.app.pipeline.calculator import DeterministicCalculator

def test_parse_numbers() -> None:
    calc = DeterministicCalculator()
    assert calc.parse_number("2,176.5") == 2176.5
    assert calc.parse_number("$450B") == 450e9
    assert calc.parse_number("€15.2M") == 15.2e6
    assert calc.parse_number("(45.5)") == -45.5
    assert calc.parse_number("-100") == -100.0
    assert calc.parse_number("8.5%") == 8.5
    assert calc.parse_number("invalid") is None

def test_percentage_change() -> None:
    calc = DeterministicCalculator()
    rec = calc.percentage_change(200.0, 250.0, "2022", "2023")
    assert rec.result == 25.0
    assert rec.unit == "%"
    assert "2022" in rec.raw_values
    assert "2023" in rec.raw_values
    assert rec.operation == "percentage_change"

def test_difference() -> None:
    calc = DeterministicCalculator()
    rec = calc.difference(250.0, 200.0, "2023", "2022", unit="USD B")
    assert rec.result == 50.0
    assert rec.unit == "USD B"

def test_aggregation_and_safe_formula() -> None:
    calc = DeterministicCalculator()
    sum_rec = calc.aggregate([10.0, 20.0, 30.0], "sum")
    assert sum_rec.result == 60.0

    mean_rec = calc.aggregate([10.0, 20.0, 30.0], "mean")
    assert mean_rec.result == 20.0

    formula_rec = calc.evaluate_safe_expression("(a + b) / 2", {"a": 10.0, "b": 30.0})
    assert formula_rec.result == 20.0

def test_safe_formula_prevents_harmful_code() -> None:
    calc = DeterministicCalculator()
    with pytest.raises(ValueError):
        # Disallow function calls or non-whitelisted AST
        calc.evaluate_safe_expression("__import__('os').system('ls')", {})

