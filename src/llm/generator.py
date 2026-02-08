import json
import os
import sys
from typing import Dict, Any, Optional

from src.llm.prompts import COREP_SYSTEM_PROMPT, COREP_USER_PROMPT_TEMPLATE
from src.retrieval.retriever import Retriever
from src.templates.ca1_template import CA1Template
from pydantic import ValidationError

# Import Providers
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class CorepGenerator:
    def __init__(self, provider="Mock", api_key=None, model_name="gpt-4o", base_url=None):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.retriever = Retriever()
        self.client = self._init_client()

    def _init_client(self):
        if self.provider == "Mock":
            return None
        
        if self.provider == "OpenAI":
            if not OpenAI: raise ImportError("OpenAI library not found")
            return OpenAI(api_key=self.api_key)
            
        if self.provider == "Anthropic":
            if not Anthropic: raise ImportError("Anthropic library not found")
            return Anthropic(api_key=self.api_key)
            
        if self.provider == "Gemini":
            if not genai: raise ImportError("Google GenerativeAI library not found")
            genai.configure(api_key=self.api_key)
            return genai
            
        if self.provider == "Ollama":
             if not OpenAI: raise ImportError("OpenAI library (for Ollama) not found")
             return OpenAI(base_url=self.base_url, api_key="ollama")

        return None

    def generate_report(self, scenario_text: str) -> Dict[str, Any]:
        # 1. Retrieve Context
        print(f"Retrieving context for: {scenario_text[:50]}...")
        retrieved_docs = self.retriever.retrieve(scenario_text, top_k=5)
        context_str = "\n\n".join([f"Source: {d['metadata']['article']}\n{d['text']}" for d in retrieved_docs])
        
        # 2. Prepare Prompt
        user_prompt = COREP_USER_PROMPT_TEMPLATE.format(
            scenario_description=scenario_text,
            context=context_str
        )

        # 3. Call LLM
        if self.provider == "Mock":
            raw_json = self._mock_response()
        else:
            raw_json = self._call_llm(user_prompt)

        # 4. Parse & Validate JSON
        try:
            # Clean markup if present
            cleaned_json = self._clean_json(raw_json)
            data_dict = json.loads(cleaned_json)
            
            # Helper to map audit trail if missing or partial (LLM sometimes lazy)
            if "audit_trail" not in data_dict:
                data_dict["audit_trail"] = {}

            # Validate with Pydantic
            # We wrap it in a try-except to catch validation errors
            template = CA1Template(**data_dict)
            
            # Auto-correct totals to ensure consistency
            template.calculate_totals()
            
            return template.model_dump()
            
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON format from LLM: {str(e)}", "raw_response": raw_json}
        except ValidationError as e:
            return {"error": f"Schema Validation Failed: {str(e)}", "raw_response": raw_json}
        except Exception as e:
            return {"error": f"Generation Error: {str(e)}", "raw_response": raw_json}

    def _call_llm(self, user_prompt: str) -> str:
        try:
            if self.provider == "OpenAI" or self.provider == "Ollama":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": COREP_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                return response.choices[0].message.content

            elif self.provider == "Anthropic":
                message = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4000,
                    system=COREP_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return message.content[0].text

            elif self.provider == "Gemini":
                model = self.client.GenerativeModel(self.model_name)
                full_prompt = f"{COREP_SYSTEM_PROMPT}\n\n{user_prompt}"
                response = model.generate_content(full_prompt, generation_config={"response_mime_type": "application/json"})
                return response.text

        except Exception as e:
            raise Exception(f"Provider {self.provider} Error: {e}")
        
        return "{}"

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _mock_response(self):
        return json.dumps({
            "row_010_own_funds": 150000000.0,
            "row_015_tier1_capital": 150000000.0,
            "row_020_cet1_capital": 150000000.0,
            "row_040_paid_up_capital": 100000000.0,
            "row_060_share_premium": 0.0,
            "row_070_own_cet1_instruments": 0.0,
            "row_130_retained_earnings": 50000000.0,
            "row_140_previous_years_retained": 50000000.0,
            "row_150_profit_or_loss_eligible": 0.0,
            "row_180_accumulated_oci": 0.0,
            "row_200_other_reserves": 0.0,
            "row_300_goodwill": 0.0,
            "row_340_intangible_assets": 0.0,
            "row_530_at1_capital": 0.0,
            "row_540_at1_instruments": 0.0,
            "row_750_tier2_capital": 0.0,
            "row_760_tier2_instruments": 0.0,
            "audit_trail": {
                "row_020_cet1_capital": {
                    "value": 150000000.0,
                    "reasoning": "Sum of paid up capital (100m) and retained earnings (50m)",
                    "source_articles": ["Article 26 CRR"],
                    "confidence": 1.0
                }
            }
        })
