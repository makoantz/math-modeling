from parser.question_parser import ParsedQuestion
import logging

logger = logging.getLogger(__name__)

class EquationSolver:
    def solve(self, parsed_data: ParsedQuestion) -> dict:
        """Solve the equations using the parsed data"""
        results = parsed_data.known_values.copy()
        logger.debug(f"Starting with known values: {results}")

        # Keep solving relationships until all variables are known
        while parsed_data.relationships:
            solved_one = False
            
            # Try each unsolved relationship
            for var_name, relationship in list(parsed_data.relationships.items()):
                base_var = relationship[0]
                value = relationship[1]
                operation = relationship[2]
                
                # Check if base variable is already solved
                if base_var in results:
                    # Calculate the new value
                    if operation == "add":
                        results[var_name] = results[base_var] + value
                    elif operation == "subtract":
                        results[var_name] = results[base_var] - value
                    
                    # Remove this relationship from the list
                    del parsed_data.relationships[var_name]
                    solved_one = True
                    logger.debug(f"Solved {var_name} = {results[var_name]}")
            
            if not solved_one and parsed_data.relationships:
                raise ValueError(f"Unable to solve remaining relationships: {parsed_data.relationships}")

        return results