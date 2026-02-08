import streamlit as st
import os
import json
import pandas as pd
from dotenv import load_dotenv

# Import Key Modules
from src.llm.generator import CorepGenerator
from src.validation.validator import Validator
from src.templates.ca1_template import CA1Template

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="PRA COREP Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Scenarios
def load_scenarios():
    path = os.path.join("data", "knowledge_base", "sample_scenarios.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

SCENARIOS = load_scenarios()

# Sidebar Configuration
with st.sidebar:
    st.title("PRA Regulatory Copilot")
    st.markdown("---")
    
    st.markdown("### LLM Configuration")
    provider = st.radio("Provider", ["OpenAI", "Anthropic", "Gemini", "Ollama", "Mock"], horizontal=True)
    
    api_key = None
    base_url = None
    model_name = "gpt-4o"

    if provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key", type="password")
        model_name = st.selectbox("Model", ["gpt-4o", "gpt-4-turbo"])
    elif provider == "Anthropic":
        api_key = st.text_input("Anthropic API Key", type="password")
        model_name = st.selectbox("Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229"])
    elif provider == "Gemini":
        api_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox("Model", [
            "gemini-2.0-flash", 
            "gemini-2.0-flash-lite-preview-02-05", 
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ])
    elif provider == "Ollama":
        base_url = st.text_input("Base URL", value="http://localhost:11434/v1")
        model_name = st.text_input("Model Name", value="llama3")
        api_key = "ollama"

    if st.button("Initialize / Update"):
        st.session_state.generator = CorepGenerator(
            provider=provider,
            api_key=api_key or os.getenv("LLM_API_KEY"),
            model_name=model_name,
            base_url=base_url
        )
        st.success(f"Initialized {provider}")

# Main Content
st.title("LLM-Assisted COREP Reporting (Prototype)")
st.markdown("Automated CA1 (Own Funds) Template Generation with RAG & Validation")

# Initialize Session State
if "generator" not in st.session_state:
    st.session_state.generator = CorepGenerator(provider="Mock") # Default to Mock
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# Input Section
col_input, col_action = st.columns([0.8, 0.2])

with col_input:
    # Scenario Selection
    scenario_names = ["Custom Query"] + [f"{s['scenario_id']}: {s['bank_name']}" for s in SCENARIOS]
    selected_scenario = st.selectbox("Select Scenario", scenario_names)
    
    default_input = ""
    if selected_scenario != "Custom Query":
        # Find selected scenario data
        s_id_str = selected_scenario.split(":")[0]
        s_data = next(s for s in SCENARIOS if s['scenario_id'] == s_id_str)
        default_input = json.dumps(s_data['input_data'], indent=2)
        st.info(f"**Description:** {s_data['description']}")
    
    user_query = st.text_area("Input Data / Query", value=default_input, height=200, 
                              placeholder="Enter JSON data or Natural Language description.\n\nExample:\n'Show CA1 for a bank with £500M paid up capital, £850M retained earnings, and £30M goodwill deduction.'")

with col_action:
    st.markdown("##") # Spacing
    if st.button("Generate Report", type="primary", use_container_width=True):
        if not user_query:
            st.warning("Please enter input data.")
        else:
            with st.spinner("Analyzing Regulations & Generating Report..."):
                # Run Generation
                result = st.session_state.generator.generate_report(user_query)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.analysis_result = result
                    st.success("Generation Complete!")

# Output Section (4 Panels)
if st.session_state.analysis_result:
    st.markdown("---")
    
    # Validation Logic
    validator = Validator()
    try:
        template_obj = CA1Template(**st.session_state.analysis_result)
        validation_output = validator.validate(template_obj)
    except Exception as e:
        validation_output = {"is_valid": False, "results": [], "error_count": 1, "warning_count": 0}
        st.error(f"Validation Error: {e}")

    # Tabs
    tab_viz, tab1, tab2, tab3, tab4 = st.tabs(["📊 Visuals", "📋 Template (CA1)", "✅ Validation", "🔍 Audit Trail", "📚 Context"])
    
    # Helper for formatting
    def fmt_millions(val):
        if isinstance(val, (int, float)):
            return f"£ {val / 1_000_000:,.2f} M"
        return val

    with tab_viz:
        st.subheader("Capital Dashboard")
        
        # 1. Key Metrics
        data = st.session_state.analysis_result
        col1, col2, col3 = st.columns(3)
        
        cet1 = data.get("row_020_cet1_capital", 0)
        t1 = data.get("row_015_tier1_capital", 0)
        own_funds = data.get("row_010_own_funds", 0)
        
        col1.metric("CET1 Capital", fmt_millions(cet1))
        col2.metric("Tier 1 Capital", fmt_millions(t1))
        col3.metric("Total Own Funds", fmt_millions(own_funds))
        
        st.markdown("### Capital Composition")
        
        # 2. Composition Chart
        # Calculate components (simplified for chart)
        at1 = data.get("row_530_at1_capital", 0)
        t2 = data.get("row_750_tier2_capital", 0)
        
        chart_data = pd.DataFrame({
            "Capital Type": ["CET1", "AT1", "Tier 2"],
            "Amount": [cet1, at1, t2]
        })
        
        st.bar_chart(chart_data.set_index("Capital Type"))

    with tab1:
        st.subheader("C 01.00 - Own Funds")
        
        # Format for display
        display_data = []
        exclude_fields = ["audit_trail"]
        
        for key, value in st.session_state.analysis_result.items():
            if key not in exclude_fields:
                formatted_val = fmt_millions(value)
                display_data.append({"Row ID": key, "Amount": formatted_val})
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("EBA Validation Rules")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", "VALID" if validation_output["is_valid"] else "INVALID", 
                 delta_color="normal" if validation_output["is_valid"] else "inverse")
        c2.metric("Errors", validation_output["error_count"])
        c3.metric("Warnings", validation_output["warning_count"])
        
        st.markdown("### Detailed Results")
        for res in validation_output["results"]:
            icon = "✅" if res["passed"] else ("❌" if res["severity"] == "ERROR" else "⚠️")
            with st.expander(f"{icon} {res['rule_id']} - {res['message']}"):
                st.write(f"Severity: {res['severity']}")

    with tab3:
        st.subheader("Audit Trail & Reasoning")
        audit_trail = st.session_state.analysis_result.get("audit_trail", {})
        
        if audit_trail:
            for field, record in audit_trail.items():
                with st.expander(f"ℹ️ {field}"):
                    if isinstance(record, dict):
                        st.markdown(f"**Value:** {fmt_millions(record.get('value'))}")
                        st.markdown(f"**Reasoning:** {record.get('reasoning')}")
                        st.markdown(f"**Sources:** {', '.join(record.get('source_articles', []))}")
                    else:
                        st.write(record)
        else:
            st.info("No detailed audit trail provided by LLM.")

    with tab4:
        st.subheader("Retrieved Regulatory Context")
        with st.spinner("Fetching context..."):
            retriever = st.session_state.generator.retriever
            docs = retriever.retrieve(user_query, top_k=5)
            
            for doc in docs:
                with st.container():
                    st.markdown(f"**{doc['metadata']['article']}** ({doc['metadata']['section']})")
                    st.caption(doc['text'])
                    st.markdown("---")


