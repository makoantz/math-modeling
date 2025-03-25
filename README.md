# README.md

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