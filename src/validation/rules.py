from src.templates.ca1_template import CA1Template
from typing import List, Dict

class ValidationResult:
    def __init__(self, rule_id: str, passed: bool, message: str, severity: str = "ERROR"):
        self.rule_id = rule_id
        self.passed = passed
        self.message = message
        self.severity = severity # ERROR or WARNING

    def to_dict(self):
        return {
            "rule_id": self.rule_id,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity
        }

def validate_ca1_r010(data: CA1Template) -> ValidationResult:
    """Rule CA1_R010: Own Funds = Tier 1 + Tier 2"""
    calculated = data.row_015_tier1_capital + data.row_750_tier2_capital
    diff = abs(data.row_010_own_funds - calculated)
    passed = diff < 1.0 # Tolerance for rounding
    
    msg = "Passed" if passed else f"Own Funds ({data.row_010_own_funds}) != Tier 1 ({data.row_015_tier1_capital}) + Tier 2 ({data.row_750_tier2_capital})"
    return ValidationResult("CA1_R010", passed, msg)

def validate_ca1_r015(data: CA1Template) -> ValidationResult:
    """Rule CA1_R015: Tier 1 = CET1 + AT1"""
    calculated = data.row_020_cet1_capital + data.row_530_at1_capital
    diff = abs(data.row_015_tier1_capital - calculated)
    passed = diff < 1.0
    
    msg = "Passed" if passed else f"Tier 1 ({data.row_015_tier1_capital}) != CET1 ({data.row_020_cet1_capital}) + AT1 ({data.row_530_at1_capital})"
    return ValidationResult("CA1_R015", passed, msg)

def validate_ca1_r020(data: CA1Template) -> ValidationResult:
    """Rule CA1_R020: CET1 = Sum of items - deductions"""
    # Simplified sum for prototype
    # CET1 = Paid Up + Share Premium + Retained Earnings + OCI + Reserves + Own Inst + Goodwill + Intangibles
    # Note: Deductions are expected to be negative values in the model
    
    items_sum = (
        data.row_040_paid_up_capital + 
        data.row_060_share_premium +
        data.row_130_retained_earnings +
        data.row_180_accumulated_oci + 
        data.row_200_other_reserves + 
        data.row_070_own_cet1_instruments + 
        data.row_300_goodwill + 
        data.row_340_intangible_assets
    )
    
    diff = abs(data.row_020_cet1_capital - items_sum)
    passed = diff < 1.0
    
    msg = "Passed" if passed else f"CET1 ({data.row_020_cet1_capital}) != Sum of components ({items_sum})"
    return ValidationResult("CA1_R020", passed, msg)

def validate_ca1_r100(data: CA1Template) -> ValidationResult:
    """Rule CA1_R100: Deductions must be negative or zero"""
    deductions = [data.row_300_goodwill, data.row_340_intangible_assets, data.row_070_own_cet1_instruments]
    failed_values = [v for v in deductions if v > 0]
    passed = len(failed_values) == 0
    
    msg = "Passed" if passed else f"Deductions must be <= 0. Found positive values: {failed_values}"
    return ValidationResult("CA1_R100", passed, msg)

def validate_ca1_r130(data: CA1Template) -> ValidationResult:
    """Rule CA1_R130: Retained Earnings = Previous + Current"""
    calculated = data.row_140_previous_years_retained + data.row_150_profit_or_loss_eligible
    diff = abs(data.row_130_retained_earnings - calculated)
    passed = diff < 1.0
    
    msg = "Passed" if passed else f"Retained Earnings ({data.row_130_retained_earnings}) != Previous ({data.row_140_previous_years_retained}) + Current ({data.row_150_profit_or_loss_eligible})"
    return ValidationResult("CA1_R130", passed, msg)

ALL_RULES = [
    validate_ca1_r010,
    validate_ca1_r015,
    validate_ca1_r020,
    validate_ca1_r100,
    validate_ca1_r130
]
