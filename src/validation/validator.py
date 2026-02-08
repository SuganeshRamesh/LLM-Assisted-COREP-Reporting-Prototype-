from src.templates.ca1_template import CA1Template
from src.validation.rules import ALL_RULES, ValidationResult
from typing import List, Dict, Any

class Validator:
    def __init__(self):
        self.rules = ALL_RULES

    def validate(self, data: CA1Template) -> Dict[str, Any]:
        """
        Runs all validation rules against the provided template data.
        Returns a summary dictionary.
        """
        results = []
        error_count = 0
        warning_count = 0
        
        for rule_func in self.rules:
            result = rule_func(data)
            results.append(result)
            if not result.passed:
                if result.severity == "ERROR":
                    error_count += 1
                else:
                    warning_count += 1
                    
        return {
            "is_valid": error_count == 0,
            "error_count": error_count,
            "warning_count": warning_count,
            "results": [r.to_dict() for r in results]
        }
