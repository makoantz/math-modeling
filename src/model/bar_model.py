class BarModel:
    def __init__(self, weights: dict):
        """Initialize bar model with weights"""
        self.weights = weights
        self.max_weight = max(weights.values())
        self.min_weight = min(weights.values())

    def get_relative_sizes(self):
        """Return the relative sizes of bars (0-1 scale)"""
        return {
            name: value/self.max_weight 
            for name, value in self.weights.items()
        }
    
    def add_variable(self, name, value):
        self.variables[name] = value
    
    def generate_bar_representation(self):
        # This method would generate a bar representation based on the variables
        bar_representation = ""
        for name, value in self.variables.items():
            bar_representation += f"{name}: {'|' * (value // 10)} ({value} grams)\n"
        return bar_representation.strip()