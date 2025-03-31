import os
import json
import logging
from expression_parser import ExpressionParser

logger = logging.getLogger(__name__)

def load_questions_from_file(file_path):
    """Load questions from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Error: Could not find file at {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error: Invalid JSON format in {file_path}")
        raise

def solve_problem(question_data):
    """Solve a math problem based on the given question data."""
    variables = {}
    unknown_variables = set(question_data["unknowns"])
    parser = ExpressionParser()
    
    # Process each variable until all unknowns are resolved
    while unknown_variables:
        progress_made = False
        
        for var_name, expression in question_data["variables"].items():
            # Skip if variable is already solved
            if var_name in variables:
                continue
            
            # Try to evaluate the expression
            try:
                if parser.can_evaluate(expression, variables):
                    logger.debug(f"Evaluating {var_name} = {expression}")
                    value = parser.evaluate(expression, variables)
                    variables[var_name] = value
                    logger.debug(f"Result: {var_name} = {value}")
                    if var_name in unknown_variables:
                        unknown_variables.remove(var_name)
                    progress_made = True
            except Exception as e:
                logger.debug(f"Failed to evaluate {var_name}: {str(e)}")
                continue
        
        # If no progress was made in this iteration, we can't solve further
        if not progress_made and unknown_variables:
            logger.error(f"Stuck variables: {unknown_variables}")
            logger.error(f"Current known variables: {variables}")
            raise ValueError(f"Could not solve for variables: {unknown_variables}")
    
    return variables