from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ParsedQuestion:
    known_values: Dict[str, float]
    relationships: Dict[str, List]
    unknowns: List[str]

class QuestionParser:
    def parse_question(self, question_data: dict) -> ParsedQuestion:
        """Parse the question data into known values and relationships"""
        variables = question_data['variables']
        known_values = {}
        relationships = {}
        
        # Get unknowns if available, otherwise initialize empty list
        unknowns = question_data.get('unknowns', [])

        # Parse variables
        for var_name, var_value in variables.items():
            if isinstance(var_value, (int, float)):
                known_values[var_name] = float(var_value)
            elif isinstance(var_value, list):
                relationships[var_name] = var_value
        
        return ParsedQuestion(
            known_values=known_values,
            relationships=relationships,
            unknowns=unknowns
        )