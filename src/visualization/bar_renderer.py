import matplotlib.pyplot as plt
import re
import numpy as np
from matplotlib.offsetbox import AnchoredText
from matplotlib.patheffects import withStroke

class BarRenderer:
    def __init__(self):
        # Define colors for different types of variables
        self.colors = {
            'known': '#2ecc71',
            'calculated': '#3498db',
            'difference': '#e74c3c',
            'part1': '#3498db',
            'part2': '#9b59b6'
        }
        self.dimension_color = '#333333'  # dark gray for dimension lines

    def get_parts(self, var_name, question_data, weights_dict):
        """Get component parts for a variable based on string expression format"""
        var_def = question_data['variables'].get(var_name)
        
        # If it's a simple value (just a number)
        if re.match(r'^-?\d+(\.\d+)?$', str(var_def)):
            return [float(var_def)], None, True
        
        # If it's a variable reference
        if var_def in weights_dict:
            return [weights_dict[var_def]], None, False
        
        # For expressions with operations
        if '+' in var_def:
            parts = var_def.split('+')
            base = parts[0].strip()
            amount = float(parts[1].strip()) if re.match(r'^-?\d+(\.\d+)?$', parts[1].strip()) else weights_dict.get(parts[1].strip(), 0)
            if base in weights_dict:
                return [weights_dict[base], amount], "add", False
        elif '-' in var_def:
            parts = var_def.split('-')
            base = parts[0].strip()
            amount = float(parts[1].strip()) if re.match(r'^-?\d+(\.\d+)?$', parts[1].strip()) else weights_dict.get(parts[1].strip(), 0)
            if base in weights_dict:
                return [weights_dict[base], amount], "subtract", False
        
        # Default case - just show the value
        return [weights_dict.get(var_name, 0)], None, False

    def render(self, bar_model, question_data=None):
        """Render the bar model using horizontal bars with architectural-style dimensions"""
        # Create figure with proper layout
        fig, (text_ax, main_ax) = plt.subplots(2, 1, figsize=(12, 10), 
                                               gridspec_kw={'height_ratios': [1, 5]})
        
        # Display the question text at the top
        if question_data:
            text_ax.text(0.5, 0.5, question_data['question'], 
                         fontsize=12, ha='center', va='center', wrap=True)
            text_ax.axis('off')
        
        # Get weights for visualization
        weights = bar_model.weights
        
        # Setup the main visualization axis
        main_ax.set_title("Bar Model Visualization")
        main_ax.set_xlim(0, bar_model.max_weight * 1.2)
        
        # Draw bars for each variable
        y_pos = len(weights)
        for name, value in weights.items():
            # Determine color based on if it's a known or calculated value
            is_known = name not in question_data.get('unknowns', [])
            color = self.colors['known'] if is_known else self.colors['calculated']
            
            # Draw the bar
            main_ax.barh(y_pos, value, height=0.6, color=color, 
                         edgecolor='black', alpha=0.7)
            
            # Add the label and value
            main_ax.text(value + 5, y_pos, f"{name}: {value}", va='center')
            
            y_pos -= 1
        
        # Set y-axis labels and remove frame
        main_ax.set_yticks([])
        main_ax.spines['top'].set_visible(False)
        main_ax.spines['right'].set_visible(False)
        main_ax.spines['left'].set_visible(False)
        
        plt.tight_layout()
        plt.show()