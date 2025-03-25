from parser.question_parser import ParsedQuestion
import logging

logger = logging.getLogger(__name__)

class EquationSolver:
    def solve(self, parsed_data: ParsedQuestion) -> dict:
        """Solve the equations using the parsed data"""
        results = parsed_data.known_values.copy()
        logger.debug(f"Starting with known values: {results}")

        # Keep solving equations until all variables are known
        while parsed_data.equations:
            solved_one = False
            # Try each unsolved equation
            for var_name, equation in list(parsed_data.equations.items()):
                try:
                    # Replace variables with known values
                    solved_equation = equation
                    for known_var, value in results.items():
                        solved_equation = solved_equation.replace(known_var, str(value))
                    
                    # Evaluate the equation
                    result = eval(solved_equation)
                    results[var_name] = result
                    del parsed_data.equations[var_name]
                    solved_one = True
                    logger.debug(f"Solved {var_name} = {result}")
                except:
                    continue
            
            if not solved_one and parsed_data.equations:
                raise ValueError(f"Unable to solve remaining equations: {parsed_data.equations}")

        return results