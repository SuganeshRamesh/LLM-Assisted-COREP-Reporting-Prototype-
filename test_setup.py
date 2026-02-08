try:
    import streamlit
    import pydantic
    import pandas
    import bs4
    import openai
    print("Imports: OK")
except ImportError as e:
    print(f"Imports: FAILED ({e})")

from core.models import OwnFundsTemplate
from core.llm_chain import CorepLLMChain

# Test Model
try:
    template = OwnFundsTemplate(alias_generator=None) # Test instantiation
    print("Models: OK")
except Exception as e:
    print(f"Models: FAILED ({e})")

# Test Chain (Mock)
try:
    chain = CorepLLMChain(api_key="mock")
    res = chain.process_scenario("Test Scenario")
    if res.get("audit_log"):
        print("Logic Chain: OK")
    else:
        print("Logic Chain: FAILED (No output)")
except Exception as e:
    print(f"Logic Chain: FAILED ({e})")
