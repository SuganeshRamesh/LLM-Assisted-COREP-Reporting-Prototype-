import pytest
from src.templates.ca1_template import CA1Template
from src.validation.validator import Validator

@pytest.fixture
def valid_data():
    return CA1Template(
        row_010_own_funds=150.0,
        row_015_tier1_capital=150.0,
        row_020_cet1_capital=150.0,
        row_040_paid_up_capital=100.0,
        row_130_retained_earnings=50.0,
        row_140_previous_years_retained=50.0,
        row_150_profit_or_loss_eligible=0.0
    )

def test_validator_pass(valid_data):
    validator = Validator()
    result = validator.validate(valid_data)
    assert result["is_valid"] == True
    assert result["error_count"] == 0

def test_rule_ca1_r010_fail(valid_data):
    # Break Own Funds = T1 + T2
    valid_data.row_010_own_funds = 200.0 # Should be 150
    validator = Validator()
    result = validator.validate(valid_data)
    
    assert result["is_valid"] == False
    assert any(r["rule_id"] == "CA1_R010" and not r["passed"] for r in result["results"])

def test_rule_ca1_r100_fail(valid_data):
    # Deductions must be negative
    valid_data.row_300_goodwill = 10.0 # Positive value error
    validator = Validator()
    result = validator.validate(valid_data)
    
    assert result["is_valid"] == False
    assert any(r["rule_id"] == "CA1_R100" and not r["passed"] for r in result["results"])
