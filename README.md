# LLM-Assisted COREP Reporting (Prototype)

An LLM-assisted solution for automating COREP regulatory reporting (specifically CA1 - Own Funds) using Retrieval-Augmented Generation (RAG) and EBA-compliant validation rules.

## Overview

This project demonstrates how Large Language Models (LLMs) can be leveraged to streamline the complex process of regulatory reporting. By combining a knowledge base of the PRA Rulebook with structured data extraction, the "PRA Regulatory Copilot" transforms raw financial data or natural language descriptions into valid EBA reporting templates.

## Key Features

- **Automated Template Generation**: converts unstructured inputs (JSON or text description) into a structured CA1 (Own Funds) template.
- **RAG Integration**: Grounds every decision in actual regulation by retrieving relevant sections from the PRA Rulebook (stored in ChromaDB) to provide context for the LLM.
- **Multi-LLM Support**: Configurable backend supporting OpenAI (GPT-4), Anthropic (Claude 3), Google (Gemini 1.5 Pro), and localized models via Ollama.
- **Validation Engine**: Post-generation validator that checks compliance with EBA validation rules and internal arithmetic consistency.
- **Audit Trail & Explainability**: Every filled cell includes a "reasoning" trace and references to the specific "source articles" used to derive the value.
- **Capital Dashboard**: Visualizes key capital metrics (CET1, Tier 1, Total Capital) and their composition.

## Architecture

The application is built on a modern Python stack:

- **Frontend**: [Streamlit](https://streamlit.io/) for an interactive, rapid-prototype UI.
- **Backend Logic**: Python 3.10+
- **Data Modeling**: [Pydantic](https://docs.pydantic.dev/) for strict schema validation and type safety.
- **Vector Store**: [ChromaDB](https://www.trychroma.com/) for storing and retrieving embeddings of the PRA Rulebook.
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` for semantic search.
- **LLM Integration**: Custom `CorepGenerator` abstraction layer to swap providers easily.

## Techniques Used

### 1. Retrieval-Augmented Generation (RAG)

We do not rely on the LLM's internal knowledge cutoffs. Instead, we inject the specific, up-to-date text of the PRA Rulebook into the prompt context at runtime. This ensures the model is "looking at" the actual rules when making classification decisions for capital instruments.

### 2. Structured Output Enforcement

Regulatory reporting requires precision. We force the LLM to output valid JSON that strictly adheres to our Pydantic schema (`CA1Template`). This eliminates hallucinated fields and ensures the output can be programmatically processed.

### 3. Self-Correction & Validation

The system doesn't just trust the LLM. It runs a deterministic validation step (`Validator` class). If the LLM's output violates a rule (e.g., *Tier 1 must equal CET1 + AT1*), the system flags it. In a future iteration, these flags can be fed back to the LLM for self-correction.

### 4. Prompt Engineering

We use a sophisticated system prompt (`prompts.py`) that instructs the model to act as a specialized Regulatory Reporting Analyst, prioritizing conservative interpretations and strict adherence to the provided context.

## Achieved Outcomes

1. **Efficiency**: Reduces the time to draft a CA1 template from hours of manual mapping to seconds.
2. **Accuracy**: The RAG approach significantly reduces hallucinations compared to standard prompting.
3. **Transparency**: The "Audit Trail" feature allows compliance officers to verify *why* a number was placed in a specific row, building trust in the AI system.
4. **Resilience**: By abstracting the LLM provider, the system is not locked into a single vendor and can switch models based on cost, latency, or data privacy requirements.

## Installation & Usage

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. **Clone the repository** (if applicable) or navigate to the project root.
2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Environment Variables**:
    Create a `.env` file in the root directory and add your API keys:

    ```env
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
    GOOGLE_API_KEY=AIza...
    ```

### Running the Application

Execute the Streamlit app:

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

### Using the Tool

1. Select a **Scenario** from the dropdown (e.g., "Standard Bank") or choose "Custom Query" to input your own data.
2. Review the **Retrieved Context** tab to see which regulations are being referenced.
3. Click **Generate Report**.
4. Explore the **Visuals**, **Template**, and **Audit Trail** tabs to analyze the results.

---
*Note: This is a prototype for demonstration purposes and should not be used for actual regulatory submissions without human review.*

