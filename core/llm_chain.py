import os
import json
from typing import Dict, Any
from .models import OwnFundsTemplate, AuditLogItem, RuleReference
from .rag import RAGPipeline
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import sys
# Attempt to handle environment mismatch where pip installs to User Roaming but python doesn't see it.
# Check for common user site-package locations (Windows)
import site
try:
    user_site_packages = site.getusersitepackages()
    if user_site_packages not in sys.path:
        sys.path.append(user_site_packages)
    
    # Explicit fallback based on user's pip output
    fallback_path = os.path.expanduser("~\\AppData\\Roaming\\Python\\Python313\\site-packages")
    if os.path.exists(fallback_path) and fallback_path not in sys.path:
        sys.path.append(fallback_path)
except Exception:
    pass

try:
    from anthropic import Anthropic
except ImportError as e:
    print(f"DEBUG: Failed to import anthropic: {e}")
    Anthropic = None

try:
    import google.generativeai as genai
except ImportError as e:
    print(f"DEBUG: Failed to import google.generativeai: {e}")
    genai = None

class CorepLLMChain:
    def __init__(self, api_key: str = None, provider: str = "OpenAI", base_url: str = None, model_name: str = "gpt-4o"):
        self.rag = RAGPipeline()
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        
        self.client = None
        self.base_url = None

        if self.provider == "Ollama":
            sys.stderr.write(f"Initializing Ollama... Check if server is running at {base_url}\n")
            self.base_url = base_url or "http://localhost:11434/v1"
            self.api_key = "ollama" 
            if OpenAI:
                self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

        elif self.provider == "Anthropic":
            if Anthropic and self.api_key:
                self.client = Anthropic(api_key=self.api_key)
        
        elif self.provider == "Gemini":
            if genai and self.api_key:
                genai.configure(api_key=self.api_key)
                self.client = "gemini_configured" # client is the module itself essentially
            elif not genai:
                print("Warning: google-generativeai library missing.")

        elif self.provider == "OpenAI":
            if OpenAI and self.api_key:
                self.client = OpenAI(api_key=self.api_key)
        
        # Mock mode doesn't need client

    def process_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        Main pipeline:
        1. Parse scenario.
        2. Retrieve relevant PRA rules.
        3. Call LLM to map scenario to Own Funds template.
        4. Return structured JSON with audit log.
        """
        # 1. Retrieve Rules
        search_query = f"Own funds capital classification {scenario}"
        retrieved_docs = self.rag.retrieve(search_query, top_k=5)
        context_str = "\n\n".join([f"source: {d['source']}\ncontent: {d['text']}" for d in retrieved_docs])

        # 2. Construct Prompt (System)
        system_prompt = """You are a PRA Regulatory Reporting Expert for UK Banks.
Populate the COREP 'Own Funds' (C 01.00) template based on the scenario and provided rules.

Output ONLY VALID JSON matching this structure:
{
  "template_data": {
    "EligibleCapital": <float>,
    "Tier1Capital": <float>,
    "CET1Capital": <float>,
    "CET1Instruments": <float>,
    "RetainedEarnings": <float>,
    "AccumulatedOCI": <float>,
    "OtherReserves": <float>
  },
  "audit_log": [
    {
      "field_id": "CET1Capital",
      "value_derived": <float>,
      "reasoning": "Explanation...",
      "references": [{"source": "DocName", "text": "Snippet"}]
    }
  ]
}
"""

        user_prompt = f"""
SCENARIO:
{scenario}

RELEVANT PRA RULEBOOK CONTEXT:
{context_str}

Generate the Regulatory Report JSON:
"""

        if not self.client and self.provider != "Mock":
             # If provider is not Mock but client failed, fall back to mock with warning
             print("Client not initialized. Falling back to mock.")
             return self._mock_response(scenario)
             
        if self.provider == "Mock":
             return self._mock_response(scenario)

        try:
            result_json = ""
            
            if self.provider == "Anthropic":
                message = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                result_json = message.content[0].text
            
            elif self.provider == "Gemini":
                try:
                    # Only some models support system instructions, but we can pass it in user prompt for compatibility
                    model = genai.GenerativeModel(self.model_name)
                    # Combine system and user prompt for robustness
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
                    result_json = response.text
                except Exception as e:
                    if "404" in str(e):
                        print(f"Gemini Model '{self.model_name}' not found. Available models:")
                        for m in genai.list_models():
                            if 'generateContent' in m.supported_generation_methods:
                                print(f"- {m.name}")
                    raise e

            else: # OpenAI / Ollama
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                result_json = response.choices[0].message.content
            
            # Clean JSON
            if "{" in result_json:
                start = result_json.find("{")
                end = result_json.rfind("}") + 1
                result_json = result_json[start:end]

            return json.loads(result_json)
            
        except Exception as e:
            print(f"LLM Chain Error: {e}")
            return {
                "error": str(e),
                "template_data": {},
                "audit_log": []
            }

    def _mock_response(self, scenario: str) -> Dict[str, Any]:
        """
        Fallback mock response if no API key is present.
        """
        return {
            "template_data": {
                "EligibleCapital": 150.0,
                "Tier1Capital": 150.0,
                "CET1Capital": 150.0,
                "CET1Instruments": 100.0,
                "RetainedEarnings": 50.0
            },
            "audit_log": [
                {
                    "field_id": "CET1Capital",
                    "value_derived": 150.0,
                    "reasoning": "Sum of ordinary shares (100) and retained earnings (50) per PRA Rulebook Article 26.",
                    "references": [
                        {"source": "pra_own_funds_scraped.txt", "text": "Article 26 Common Equity Tier 1 items..."}
                    ]
                }
            ]
        }
