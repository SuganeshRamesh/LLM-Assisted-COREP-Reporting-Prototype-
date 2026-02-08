from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any

class AuditRecord(BaseModel):
    """
    Represents the audit trail for a single field.
    """
    value: float
    reasoning: str
    source_articles: List[str]
    confidence: float = Field(default=1.0)

class CA1Template(BaseModel):
    """
    CA1 (Own Funds) Template structure matching the project requirements.
    """
    # Row 010: Own Funds
    row_010_own_funds: float = Field(..., description="Own funds eligible for covering the pillar 1 requirements")
    
    # Row 015: Tier 1 Capital
    row_015_tier1_capital: float = Field(..., description="Tier 1 capital")
    
    # Row 020: CET1 Capital
    row_020_cet1_capital: float = Field(..., description="Common Equity Tier 1 capital")
    
    # Row 040: Paid up capital instruments
    row_040_paid_up_capital: float = Field(0.0, description="Capital instruments eligible as CET1 Capital")
    
    # Row 060: Share premium
    row_060_share_premium: float = Field(0.0, description="Share premium accounts related to CET1 instruments")
    
    # Row 070: Own CET1 instruments (Deduction)
    row_070_own_cet1_instruments: float = Field(0.0, description="Own CET1 instruments held by the institution (negative value)")
    
    # Row 130: Retained Earnings
    row_130_retained_earnings: float = Field(0.0, description="Retained earnings")
    
    # Row 140: Previous years retained earnings
    row_140_previous_years_retained: float = Field(0.0, description="Retained earnings from previous years")
    
    # Row 150: Profit or Loss eligible
    row_150_profit_or_loss_eligible: float = Field(0.0, description="Profit or loss eligible for the current financial year")
    
    # Row 180: Accumulated OCI
    row_180_accumulated_oci: float = Field(0.0, description="Accumulated other comprehensive income")
    
    # Row 200: Other Reserves
    row_200_other_reserves: float = Field(0.0, description="Other reserves")
    
    # Row 300: Goodwill (Deduction)
    row_300_goodwill: float = Field(0.0, description="Goodwill (negative value)")
    
    # Row 340: Other Intangible Assets (Deduction)
    row_340_intangible_assets: float = Field(0.0, description="Other intangible assets (negative value)")
    
    # Row 530: AT1 Capital
    row_530_at1_capital: float = Field(0.0, description="Additional Tier 1 Capital")
    
    # Row 540: AT1 Instruments
    row_540_at1_instruments: float = Field(0.0, description="Capital instruments eligible as AT1 Capital")
    
    # Row 750: Tier 2 Capital
    row_750_tier2_capital: float = Field(0.0, description="Tier 2 Capital")
    
    # Row 760: Tier 2 Instruments
    row_760_tier2_instruments: float = Field(0.0, description="Capital instruments and subordinated loans eligible as Tier 2 Capital")

    # Audit Trail
    audit_trail: Dict[str, AuditRecord] = Field(default_factory=dict, description="Audit trail for each field")

    class Config:
        validate_assignment = True

    def calculate_totals(self):
        """
        Auto-calculates aggregates based on components to ensure consistency.
        """
        # 1. Calculate CET1 (Row 020)
        # CET1 = Paid Up (040) + Share Premium (060) + Retained Earnings (130) + 
        #        Accumulated OCI (180) + Other Reserves (200) + 
        #        Adjustments (070, 300, 340 which are deductions/negative)
        self.row_130_retained_earnings = self.row_140_previous_years_retained + self.row_150_profit_or_loss_eligible
        
        self.row_020_cet1_capital = (
            self.row_040_paid_up_capital + 
            self.row_060_share_premium +
            self.row_130_retained_earnings +
            self.row_180_accumulated_oci +
            self.row_200_other_reserves +
            self.row_070_own_cet1_instruments + # deduction
            self.row_300_goodwill +             # deduction
            self.row_340_intangible_assets      # deduction
        )

        # 2. Calculate AT1 (Row 530)
        # AT1 = AT1 Instruments (540)
        self.row_530_at1_capital = self.row_540_at1_instruments

        # 3. Calculate Tier 1 (Row 015)
        # Tier 1 = CET1 (020) + AT1 (530)
        self.row_015_tier1_capital = self.row_020_cet1_capital + self.row_530_at1_capital

        # 4. Calculate Tier 2 (Row 750)
        # Tier 2 = T2 Instruments (760)
        self.row_750_tier2_capital = self.row_760_tier2_instruments

        # 5. Calculate Own Funds (Row 010)
        # Own Funds = Tier 1 (015) + Tier 2 (750)
        self.row_010_own_funds = self.row_015_tier1_capital + self.row_750_tier2_capital
