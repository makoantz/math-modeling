from dataclasses import dataclass
from typing import Dict

@dataclass
class ParsedQuestion:
    known_values: Dict[str, float]
    equations: Dict[str, str]

class QuestionParser:
    def parse_question(self, question_data: dict) -> ParsedQuestion:
        """Parse the question data into known values and equations"""
        variables = question_data['variables']
        known_values = {}
        equations = {}

        # Separate known values from equations
        for var_name, value in variables.items():
            if isinstance(value, (int, float)):
                known_values[var_name] = float(value)
            elif isinstance(value, str):
                equations[var_name] = value

        return ParsedQuestion(
            known_values=known_values,
            equations=equations
        )