import os
import json
import logging
import importlib

# Force reload modules to ensure latest changes are used
from parser import question_parser
from solver import equation_solver
from model import bar_model
from visualization import bar_renderer

importlib.reload(question_parser)
importlib.reload(equation_solver)
importlib.reload(bar_model)
importlib.reload(bar_renderer)

from parser.question_parser import QuestionParser
from solver.equation_solver import EquationSolver
from model.bar_model import BarModel
from visualization.bar_renderer import BarRenderer

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    # Get absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    data_path = os.path.join(parent_dir, 'data', 'questions.json')

    logger.debug(f"Looking for questions.json at: {data_path}")

    # Load questions from JSON file
    try:
        with open(data_path, 'r') as file:
            questions = json.load(file)
            logger.debug(f"Loaded questions: {questions}")
    except FileNotFoundError:
        logger.error(f"Error: Could not find questions.json at {data_path}")
        print("Please ensure the data folder exists with questions.json")
        return

    # Initialize components
    parser = QuestionParser()
    solver = EquationSolver()
    renderer = BarRenderer()

    for question in questions['questions']:
        logger.debug(f"Processing question: {question}")
        # Parse the question
        parsed_data = parser.parse_question(question)
        logger.debug(f"Parsed data: {parsed_data}")
        
        # Solve the equations based on parsed data
        weights = solver.solve(parsed_data)
        logger.debug(f"Solved weights: {weights}")
        
        # Generate the bar model
        bar_model = BarModel(weights)
        
        # Render the bar model with question data
        renderer.render(bar_model, question)

if __name__ == "__main__":
    main()