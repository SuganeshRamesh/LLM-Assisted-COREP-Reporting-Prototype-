import pytest
from src.templates.ca1_template import CA1Template
from pydantic import ValidationError

def test_model_creation():
    data = CA1Template(
        row_010_own_funds=100,
        row_015_tier1_capital=100,
        row_020_cet1_capital=100
    )
    assert data.row_010_own_funds == 100.0

def test_model_validation_error():
    with pytest.raises(ValidationError):
        CA1Template(
            row_010_own_funds="invalid", # String instead of float
            row_015_tier1_capital=100,
            row_020_cet1_capital=100
        )
