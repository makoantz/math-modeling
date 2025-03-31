import re

class ExpressionParser:
    """A simple parser for basic mathematical expressions with variables."""
    
    def __init__(self):
        pass
    
    def evaluate(self, expression, variables):
        """Evaluate a string expression using the values of variables."""
        # If the expression is just a number, return it
        if re.match(r'^-?\d+(\.\d+)?$', str(expression)):
            return float(expression)
        
        # For simple variable reference
        if expression in variables:
            return variables[expression]
        
        # For expressions with operations
        # First, replace all variables with their values
        result_expr = str(expression)
        for var_name, var_value in sorted(variables.items(), key=lambda x: len(x[0]), reverse=True):
            # Use word boundaries in regex to avoid partial matches
            result_expr = re.sub(r'\b' + re.escape(var_name) + r'\b', str(var_value), result_expr)
        
        # Check if all variables have been replaced
        if re.search(r'[a-zA-Z_]', result_expr):
            # Still contains variables we don't have values for
            raise ValueError(f"Cannot evaluate: {expression} - missing variables")
        
        # Evaluate the numeric expression
        try:
            return eval(result_expr)
        except Exception as e:
            raise ValueError(f"Error evaluating {result_expr}: {str(e)}")
    
    def can_evaluate(self, expression, variables):
        """Check if all variables in an expression have values."""
        # If it's a number or in variables, we can evaluate it
        if re.match(r'^-?\d+(\.\d+)?$', str(expression)) or expression in variables:
            return True
        
        # Find all variable names in the expression
        var_names = set(re.findall(r'[a-zA-Z_]+', str(expression)))
        
        # Check if all variables are defined
        return all(var_name in variables for var_name in var_names)