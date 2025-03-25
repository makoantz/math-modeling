import matplotlib.pyplot as plt
import numpy as np
import textwrap
from matplotlib.offsetbox import AnchoredText
from matplotlib.patheffects import withStroke

class BarRenderer:
    def __init__(self):
        # Define colors for different types of variables
        self.colors = {
            'known': '#2ecc71',      # green
            'calculated': '#3498db',  # blue
            'difference': '#e74c3c',  # red
            'part1': '#3498db',       # blue
            'part2': '#9b59b6'        # purple
        }
        self.dimension_color = '#333333'  # dark gray for dimension lines

    def get_parts(self, var_name, question_data, weights_dict):
        """Get component parts for a variable based on new JSON structure"""
        var_def = question_data['variables'].get(var_name)
        
        if isinstance(var_def, (int, float)):
            # It's a simple value
            return [float(var_def)], None, True
        elif isinstance(var_def, list):
            # It's a relationship
            base_var, amount, operation = var_def
            base_value = weights_dict.get(base_var, 0)
            
            if operation == "add":
                return [base_value, amount], "add", False  # False means base is not a direct value
            elif operation == "subtract":
                return [base_value, -amount], "subtract", False
        
        return [weights_dict.get(var_name, 0)], None, False

    def render(self, bar_model, question_data=None):
        """Render the bar model using horizontal bars with architectural-style dimensions"""
        # Create figure with proper layout
        fig, (text_ax, main_ax) = plt.subplots(2, 1, figsize=(12, 10), 
                                               gridspec_kw={'height_ratios': [1, 5]})
        
        # Convert bar_model.weights to a dictionary if it's not already
        if isinstance(bar_model.weights, dict):
            weights_dict = bar_model.weights
        else:
            # Create a dictionary from the list assuming names match question_data variables
            names = list(question_data['variables'].keys())
            weights_dict = {name: value for name, value in zip(names, bar_model.weights)}
        
        # Get unknowns
        unknowns = question_data.get('unknowns', []) if question_data else []
        
        # Add problem statement at the top in its own axis
        if question_data and 'question' in question_data:
            # Wrap text to fit in figure
            wrapped_text = textwrap.fill(question_data['question'], width=80)
            # Create a text box with the problem statement
            text_ax.text(0.5, 0.5, wrapped_text, ha='center', va='center', 
                         fontsize=12, wrap=True, bbox=dict(
                             boxstyle='round,pad=1.0',
                             facecolor='#f8f9fa',
                             alpha=0.8,
                             edgecolor='#dee2e6'))
            # Remove axis elements from the text axis
            text_ax.axis('off')
        else:
            text_ax.axis('off')
        
        # Calculate bar height based on number of items
        bar_height = 0.5
        names = list(weights_dict.keys())
        y_pos = np.arange(len(names), 0, -1)  # Reversed to show from top to bottom
        
        # Process each bar
        for i, name in enumerate(names):
            bar_y = y_pos[i]
            total_value = weights_dict[name]
            
            # Get parts and operation type
            if question_data and 'variables' in question_data:
                parts, operation, is_direct = self.get_parts(name, question_data, weights_dict)
            else:
                parts = [total_value]
                operation = None
                is_direct = True
            
            # Draw the bar segments
            if len(parts) > 1:
                # First segment
                main_ax.barh(bar_y, parts[0], align='center', 
                             color=self.colors['known'], height=bar_height)
                
                # Second segment (difference)
                color = self.colors['part2'] if parts[1] > 0 else self.colors['difference']
                left = parts[0] if parts[1] > 0 else parts[0] + parts[1]
                width = abs(parts[1])
                main_ax.barh(bar_y, width, left=left, align='center', 
                             color=color, height=bar_height)
                
                # Only add direct numeric values inside bars
                # First part is never labeled (according to requirements)
                
                # Second part is always a direct value from the JSON definition
                if abs(parts[1]) > 0:
                    main_ax.text(left + width/2, bar_y, f'{abs(parts[1]):.0f}', 
                            ha='center', va='center', color='white', fontweight='bold')
            else:
                # Single segment bar
                main_ax.barh(bar_y, parts[0], align='center', 
                           color=self.colors['known'], height=bar_height)
                
                # Only add value inside if it's a direct value and not an unknown
                if is_direct and name not in unknowns:
                    main_ax.text(parts[0]/2, bar_y, f'{parts[0]:.0f}', 
                              ha='center', va='center', color='white', fontweight='bold')
                elif name in unknowns:
                    main_ax.text(parts[0]/2, bar_y, "?", 
                              ha='center', va='center', color='white', fontsize=14, fontweight='bold')
            
            # Architectural-style dimensioning
            dimension_y_offset = -0.35
            dimension_y = bar_y + dimension_y_offset
            
            # Draw extension lines
            main_ax.vlines(x=0, ymin=bar_y-bar_height/2, ymax=dimension_y, 
                         color=self.dimension_color, linestyle='-', linewidth=1)
            main_ax.vlines(x=total_value, ymin=bar_y-bar_height/2, ymax=dimension_y, 
                         color=self.dimension_color, linestyle='-', linewidth=1)
            
            # Draw dimension line
            main_ax.hlines(y=dimension_y, xmin=0, xmax=total_value, 
                         color=self.dimension_color, linestyle='-', linewidth=1)
            
            # Add small tick marks
            tick_size = 0.06
            main_ax.vlines(x=0, ymin=dimension_y-tick_size, ymax=dimension_y+tick_size, 
                         color=self.dimension_color, linewidth=1)
            main_ax.vlines(x=total_value, ymin=dimension_y-tick_size, ymax=dimension_y+tick_size, 
                         color=self.dimension_color, linewidth=1)
            
            # Add dimension text - show "?" for unknowns, otherwise show the value
            if name in unknowns:
                label_text = "?"
            else:
                label_text = f'{total_value:g}g'
                
            main_ax.text(total_value/2, dimension_y-0.1, label_text, 
                       ha='center', va='top', color=self.dimension_color, fontsize=9)
        
        # Set up axis
        main_ax.set_yticks(y_pos)
        main_ax.set_yticklabels(names)
        main_ax.set_xlabel('Weight (grams)')
        
        # Set y-axis limits to accommodate dimensions and ensure no overlap
        spacing = 1.0 + 0.1 * len(names)
        main_ax.set_ylim(min(y_pos) + dimension_y_offset - spacing, max(y_pos) + 0.5)
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, color=self.colors['known'], label='Base Value'),
            plt.Rectangle((0,0),1,1, color=self.colors['part2'], label='Added Value'),
            plt.Rectangle((0,0),1,1, color=self.colors['difference'], label='Subtracted Value')
        ]
        main_ax.legend(handles=legend_elements, loc='lower right')
        
        # Add grid and clean up appearance
        main_ax.grid(True, axis='x', linestyle='--', alpha=0.5)
        main_ax.spines['top'].set_visible(False)
        main_ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.show()