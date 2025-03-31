# README.md
# 31 March 2025 Update

Math Modeling Application
   This project is an interactive application designed to solve math modeling problems and visualize them using bar representations. The application loads questions in JSON format, extracts variables and their relationships, solves the problems, and generates visual models to represent the solutions.

Project Structure

math-modeling/
├── src/
│   ├── main.py                 # Entry point of the application
│   ├── expression_parser.py    # Parses and evaluates mathematical expressions
│   ├── model/
│   │   ├── __init__.py         # Package initialization
│   │   └── bar_model.py        # Represents the mathematical model using bars
│   └── visualization/
│       ├── __init__.py         # Package initialization
│       └── bar_renderer.py     # Visualizes the bar model
├── data/
│   └── questions.json          # JSON formatted questions
└── README.md                   # Project documentation

Setup Instructions
1. Clone the repository:
   git clone <repository-url>
   cd math-modeling

2. Install the required dependencies:
   pip install matplotlib

3. Run the application:
   python src/main.py

Question Format
Questions are defined in JSON format with the following structure:
{
  "questions": [
    {
      "question": "A mango is 215 grams. A papaya is 185 grams heavier than the mango while the grapefruit is 154 grams lighter than the papaya. How much does the papaya weigh? How much does the grapefruit weigh?",
      "variables": {
        "mango": "215",
        "papaya": "mango+185",
        "grapefruit": "papaya-154"
      },
      "unknowns": ["papaya", "grapefruit"]
    }
  ]
}

Expression Format

Variables can be defined using the following formats:

Fixed values: "mango": "215"
Reference to other variables with operations: "papaya": "mango+185"
Complex expressions: "basket": "2*watermelon+3*orange+5*banana"
Supported operations:

   Addition: +
   Subtraction: -
   Multiplication: *
   Division: /
How It Works
   1. Loading Questions: The application loads the questions from the JSON file.
   2. Evaluating Expressions: For each question, the expression parser evaluates each variable in order, resolving dependencies.
   3. Visualization: Once the values are calculated, the bar renderer creates a visual representation of the solution.

Example Question Solutions
For the question about fruits:
   A mango is 215 grams. A papaya is 185 grams heavier than the mango while the grapefruit is 154 grams lighter than the papaya. How much does the papaya weigh? How much does the grapefruit weigh?

The application will:

1. Set mango = 215
2. Calculate papaya = mango + 185 = 215 + 185 = 400
3. Calculate grapefruit = papaya - 154 = 400 - 154 = 246
4. Display the results visually using bar models

Contributing
Feel free to submit issues or pull requests to improve the application.

# Initial Release
# Singapore Math Model Application

This project is an interactive application designed to assist users in solving Singapore Math modeling problems using bar representations. The application allows users to load questions in JSON format, parse the variables, solve the problems, and generate visual models to represent the solutions.

## Project Structure

```
singapore-math-model
├── src
│   ├── main.py               # Entry point of the application
│   ├── parser
│   │   ├── __init__.py       # Package initialization
│   │   └── question_parser.py # Parses questions to extract variables
│   ├── model
│   │   ├── __init__.py       # Package initialization
│   │   └── bar_model.py      # Represents the mathematical model using bars
│   ├── solver
│   │   ├── __init__.py       # Package initialization
│   │   └── equation_solver.py # Solves equations based on parsed variables
│   └── visualization
│       ├── __init__.py       # Package initialization
│       └── bar_renderer.py    # Visualizes the bar model
├── data
│   └── questions.json         # JSON formatted questions
├── tests
│   ├── __init__.py           # Package initialization
│   ├── test_parser.py         # Unit tests for QuestionParser
│   ├── test_model.py          # Unit tests for BarModel
│   └── test_solver.py         # Unit tests for EquationSolver
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd singapore-math-model
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage Example

Load your questions in the `data/questions.json` file in the following format:

```json
[
    {
        "question": "A mango is 165 grams. A papaya is 120 grams heavier than the mango while the grapefruit is 45 grams lighter than the papaya. How much does the papaya weigh? How much does the grapefruit weigh?"
    }
]
```

The application will parse the question, solve for the weights, and visualize the results using bar representations.

## Contributing

Feel free to submit issues or pull requests to improve the application.

