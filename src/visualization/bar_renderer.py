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

    def extract_parts(self, equation, values):
        """Extract parts from equation"""
        if '+' in equation:
            parts = equation.split('+')
            return [values.get(parts[0].strip(), 0), float(parts[1].strip())]
        elif '-' in equation:
            parts = equation.split('-')
            return [values.get(parts[0].strip(), 0), -float(parts[1].strip())]
        return [values.get(equation.strip(), 0)]

    def render(self, bar_model, question_data=None):
        """Render the bar model using horizontal bars with architectural-style dimensions"""
        # Create figure with proper layout
        fig, (text_ax, main_ax) = plt.subplots(2, 1, figsize=(12, 10), 
                                               gridspec_kw={'height_ratios': [1, 5]})
        
        # Get data
        names = list(bar_model.weights.keys())
        values = list(bar_model.weights.values())
        
        # Keep track of which variables are known vs calculated
        known_vars = {}
        if question_data and 'variables' in question_data:
            for name, val in question_data['variables'].items():
                known_vars[name] = isinstance(val, (int, float))
        
        # Prepare data for stacked bars
        y_pos = np.arange(len(names), 0, -1)  # Reversed to show from top to bottom
        base_values = []
        difference_values = []
        
        # Extract parts of equations
        for name in names:
            if question_data and 'variables' in question_data:
                var_value = question_data['variables'].get(name)
                if isinstance(var_value, str):
                    parts = self.extract_parts(var_value, bar_model.weights)
                    if len(parts) > 1:
                        base_values.append(parts[0])
                        difference_values.append(parts[1])
                    else:
                        base_values.append(parts[0])
                        difference_values.append(0)
                else:
                    base_values.append(values[names.index(name)])
                    difference_values.append(0)
            else:
                base_values.append(values[names.index(name)])
                difference_values.append(0)
        
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
        
        # Create the bars in the main axis
        base_bars = main_ax.barh(y_pos, base_values, align='center', color=self.colors['known'], 
                          label='Base Value', height=bar_height)
                
        # Add values/question marks inside the base bars only if they're known
        for i, (bar, name) in enumerate(zip(base_bars, names)):
            if known_vars.get(name, False):
                width = bar.get_width()
                if width > 0:
                    main_ax.text(width/2, bar.get_y() + bar_height/2, f'{width:.0f}', 
                            ha='center', va='center', color='white', fontweight='bold')
            else:
                # Add question mark for unknowns
                main_ax.text(bar.get_width()/2, bar.get_y() + bar_height/2, "?", 
                        ha='center', va='center', color='white', fontsize=14, fontweight='bold')
        
        # Add difference parts if they exist
        difference_bars = []
        has_differences = any(diff != 0 for diff in difference_values)
        if has_differences:
            # Calculate left edges for the difference bars
            lefts = [base if diff > 0 else base + diff for base, diff in zip(base_values, difference_values)]
            # Calculate widths for the difference bars (absolute values)
            widths = [abs(diff) for diff in difference_values]
            
            # Only add non-zero differences
            for i, (left, width, diff) in enumerate(zip(lefts, widths, difference_values)):
                if width > 0:
                    color = self.colors['part2'] if diff > 0 else self.colors['difference']
                    diff_bar = main_ax.barh(y_pos[i], width, left=left, color=color, height=bar_height)
                    difference_bars.append(diff_bar)
                    
                    # Add absolute value in the center of the difference bar (for all difference bars)
                    main_ax.text(left + width/2, y_pos[i], f'{abs(diff):.0f}', 
                            ha='center', va='center', color='white', fontweight='bold')
        
        # Architectural-style dimensioning
        dimension_y_offset = -0.35  # Reduced offset to prevent overlap
        
        for i, (name, value) in enumerate(zip(names, values)):
            bar_y = y_pos[i]
            dimension_y = bar_y + dimension_y_offset
            
            # Draw extension lines
            main_ax.vlines(x=0, ymin=bar_y-bar_height/2, ymax=dimension_y, color=self.dimension_color, linestyle='-', linewidth=1)
            main_ax.vlines(x=value, ymin=bar_y-bar_height/2, ymax=dimension_y, color=self.dimension_color, linestyle='-', linewidth=1)
            
            # Draw dimension line
            main_ax.hlines(y=dimension_y, xmin=0, xmax=value, color=self.dimension_color, linestyle='-', linewidth=1)
            
            # Add small tick marks
            tick_size = 0.06
            main_ax.vlines(x=0, ymin=dimension_y-tick_size, ymax=dimension_y+tick_size, color=self.dimension_color, linewidth=1)
            main_ax.vlines(x=value, ymin=dimension_y-tick_size, ymax=dimension_y+tick_size, color=self.dimension_color, linewidth=1)
            
            # Add dimension text
            main_ax.text(value/2, dimension_y-0.1, f'{value:g}g', ha='center', va='top', color=self.dimension_color, fontsize=9)
        
        # Set up axis
        main_ax.set_yticks(y_pos)
        main_ax.set_yticklabels(names)
        main_ax.set_xlabel('Weight (grams)')
        
        # Set y-axis limits to accommodate dimensions and ensure no overlap
        spacing = 1.0 + 0.1 * len(names)  # Adjust based on number of bars
        main_ax.set_ylim(min(y_pos) + dimension_y_offset - spacing, max(y_pos) + 0.5)
        
        # Add legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, color=self.colors['known'], label='Known/Base Value'),
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