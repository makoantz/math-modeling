import os
import json
import logging
import re
from expression_parser import ExpressionParser
from model.bar_model import BarModel
from visualization.bar_renderer import BarRenderer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_questions(file_path):
    """Load questions from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Error: Could not find questions.json at {file_path}")
        print("Please ensure the data folder exists with questions.json")
        return None

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

def visualize_solution(question_data, results):
    """Create and display a bar model visualization of the solution."""
    # Create a bar model with the results
    bar_model = BarModel(results)
    
    # Create a renderer and display the bar model
    renderer = BarRenderer()
    renderer.render(bar_model, question_data)

def main():
    """Main function to load and solve questions."""
    # Get absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_path = os.path.join(parent_dir, 'data', 'questions.json')

    logger.debug(f"Looking for questions.json at: {data_path}")

    questions = load_questions(data_path)
    if not questions:
        return
    
    for i, question in enumerate(questions["questions"]):
        print(f"Question {i+1}: {question['question']}")
        
        try:
            results = solve_problem(question)
            
            print("Solution:")
            for var in question["unknowns"]:
                print(f"{var} = {results[var]}")
                
            # Visualize the solution with a bar model
            visualize_solution(question, results)
            
        except Exception as e:
            print(f"Error solving problem: {e}")
        
        print("-" * 50)
        
        # Close any open plots before moving to the next question
        import matplotlib.pyplot as plt
        plt.close('all')

if __name__ == "__main__":
    main()