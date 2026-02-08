from pydantic import BaseModel, Field
from typing import List, Optional

class RuleReference(BaseModel):
    """
    Represents a citation from the PRA Rulebook or EBA Instructions.
    """
    source: str = Field(..., description="The source document (e.g., 'PRA Rulebook Own Funds', 'CRR Art 26')")
    text: str = Field(..., description="The relevant snippet of text justifying the decision.")
    similarity_score: Optional[float] = None

class AuditLogItem(BaseModel):
    """
    Captures the reasoning for a specific field's value.
    """
    field_id: str
    value_derived: float
    reasoning: str
    references: List[RuleReference]

class OwnFundsTemplate(BaseModel):
    """
    Simplified C 01.00 (Own Funds) Template Schema.
    Based on EBA ITS Annex I.
    """
    # Using aliases to match the template row/col IDs often used in XBRL/DPM
    # Row 010: Eligible Capital
    r010_c010: Optional[float] = Field(None, alias="EligibleCapital", description="Own funds eligible for covering the pillar 1 requirements")
    
    # Row 020: Tier 1 Capital
    r020_c010: Optional[float] = Field(None, alias="Tier1Capital", description="Tier 1 capital")
    
    # Row 030: CET1 Capital
    r030_c010: Optional[float] = Field(None, alias="CET1Capital", description="Common Equity Tier 1 capital")
    
    # Row 040: Capital Instruments eligible as CET1
    r040_c010: Optional[float] = Field(None, alias="CET1Instruments", description="Capital instruments eligible as CET1 Capital")
    
    # Row 050: Retained Earnings
    r050_c010: Optional[float] = Field(None, alias="RetainedEarnings", description="Retained earnings")
    
    # Row 060: Accumulated Other Comprehensive Income
    r060_c010: Optional[float] = Field(None, alias="AccumulatedOCI", description="Accumulated other comprehensive income")
    
    # Row 070: Other Reserves
    r070_c010: Optional[float] = Field(None, alias="OtherReserves", description="Other reserves")
    
    # Row 520: Total Risk Exposure Amount (simplified placement)
    r520_c010: Optional[float] = Field(None, alias="TotalRiskExposure", description="Total Risk Exposure Amount")

    class Config:
        populate_by_name = True
