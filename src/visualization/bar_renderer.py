import matplotlib.pyplot as plt
import re
import numpy as np
from matplotlib.offsetbox import AnchoredText
from matplotlib.patheffects import withStroke
import logging

logger = logging.getLogger(__name__)

class BarRenderer:
    def __init__(self):
        self.item_colors = plt.get_cmap('tab10').colors
        self.variable_color_map = {}
        self.color_index = 0
        self.dimension_color = '#333333'
        self.label_color = '#000000'
        self.equation_color = '#444444'
        self.hatch_color = '#888888' # Color for difference/subtracted part hatching

    def _reset_colors(self):
        """Resets color mapping for a new question."""
        self.variable_color_map = {}
        self.color_index = 0

    def _get_color_for_variable(self, var_name, alpha=0.8):
        """Assigns a consistent color to each variable name."""
        if var_name not in self.variable_color_map:
            # Cycle through base colors, avoid gray-like colors if possible from palette
            base_color = self.item_colors[self.color_index % len(self.item_colors)]
            self.variable_color_map[var_name] = base_color
            self.color_index += 1
        # Return RGBA tuple
        rgb = plt.cm.colors.to_rgb(self.variable_color_map[var_name])
        return (*rgb, alpha)

    def _add_dimension_line(self, ax, x_start, x_end, y_base, label_text, offset=0.4):
        """Adds a dimension line with ticks and label above a bar segment."""
        y_dim = y_base + offset
        y_tick_end = y_base + 0.3 # End of vertical tick just above bar

        # Vertical ticks
        ax.plot([x_start, x_start], [y_tick_end, y_dim], color=self.dimension_color, linestyle='-', linewidth=1)
        ax.plot([x_end, x_end], [y_tick_end, y_dim], color=self.dimension_color, linestyle='-', linewidth=1)
        # Horizontal line
        ax.plot([x_start, x_end], [y_dim, y_dim], color=self.dimension_color, linestyle='-', linewidth=1)
        # Label text
        mid_x = x_start + (x_end - x_start) / 2
        ax.text(mid_x, y_dim + 0.05, label_text, ha='center', va='bottom', fontsize=9, color=self.dimension_color)

    def _add_leader_label(self, ax, x_pos, y_pos, label_text, value, max_x):
        """Adds a label with a leader line pointing to the end of the bar."""
        # Position text to the right of the bar, slightly offset vertically
        text_x = value + max_x * 0.03 # Place text slightly away from bar end
        text_y = y_pos

        # Clamp text_x if it goes too far right? Or let axis limit handle it.
        # Draw the text label
        t = ax.text(text_x, text_y, label_text, va='center', ha='left', fontsize=10, color=self.label_color)

        # Draw leader line from text towards the end of the bar
        label_bbox = t.get_window_extent(renderer=ax.figure.canvas.get_renderer())
        label_width = label_bbox.width / ax.figure.dpi * (ax.get_xlim()[1] / ax.figure.get_figwidth()) # Approximate label width in data coords
        label_height = label_bbox.height / ax.figure.dpi * (ax.get_ylim()[1] / ax.figure.get_figheight())

        # Point from just left of the text towards the bar end
        leader_start_x = text_x - max_x*0.005 # Start slightly to the left of text
        leader_start_y = text_y
        leader_end_x = min(value + max_x*0.01, leader_start_x) # Point towards end, don't overlap text
        leader_end_y = y_pos

        # Simple line for now
        # ax.plot([leader_start_x, leader_end_x], [leader_start_y, leader_end_y], color=self.label_color, linewidth=0.8)
        # Optionally, point directly to the bar end if space allows
        ax.plot([text_x - max_x*0.005, value], [text_y, y_pos], color=self.label_color, linewidth=0.8, linestyle=':')


    def _add_equation(self, ax, y_pos, definition, result_value, var_name):
        """Adds the formatted equation below the bar."""
        # Replace operators with spaces for readability
        equation_str = definition.replace("*", " * ").replace("+", " + ").replace("-", " - ").replace("/", " / ")
        result_str = f"{var_name} = {equation_str} = {result_value:.1f}"
        ax.text(0, y_pos - 0.6, f"Equation: {result_str}", va='top', ha='left', fontsize=9, color=self.equation_color)


    def _parse_simple_expression(self, expression_string, all_vars_values):
        """Parses simple expressions like 'varA + 10', 'varB - 5', 'varC / 2'."""
        expression_string = str(expression_string).strip()

        # Addition: var + num or num + var
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\+\s*(\d+(?:\.\d+)?)$', expression_string)
        if match:
            var, num = match.groups()
            if var in all_vars_values:
                return {'type': 'add', 'base_var': var, 'diff_val': float(num), 'base_val': all_vars_values[var]}
        match = re.match(r'(\d+(?:\.\d+)?)\s*\+\s*([a-zA-Z_][a-zA-Z0-9_]*)$', expression_string)
        if match:
             num, var = match.groups()
             if var in all_vars_values:
                return {'type': 'add', 'base_var': var, 'diff_val': float(num), 'base_val': all_vars_values[var]}

        # Subtraction: var - num
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*-\s*(\d+(?:\.\d+)?)$', expression_string)
        if match:
            var, num = match.groups()
            if var in all_vars_values:
                return {'type': 'subtract', 'base_var': var, 'diff_val': float(num), 'base_val': all_vars_values[var]}

        # Division: var / num
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*/\s*(\d+(?:\.\d+)?)$', expression_string)
        if match:
            var, num = match.groups()
            if var in all_vars_values:
                 return {'type': 'divide', 'base_var': var, 'divisor': float(num), 'base_val': all_vars_values[var]}

        # Multiplication: var * num or num * var
        match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*(\d+(?:\.\d+)?)$', expression_string)
        if match:
            var, num = match.groups()
            if var in all_vars_values:
                 return {'type': 'multiply', 'base_var': var, 'multiplier': float(num), 'base_val': all_vars_values[var]}
        match = re.match(r'(\d+(?:\.\d+)?)\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)$', expression_string)
        if match:
             num, var = match.groups()
             if var in all_vars_values:
                 return {'type': 'multiply', 'base_var': var, 'multiplier': float(num), 'base_val': all_vars_values[var]}

        # Simple variable reference
        if expression_string in all_vars_values:
             return {'type': 'reference', 'base_var': expression_string, 'base_val': all_vars_values[expression_string]}

        # Simple number
        if re.match(r'^-?\d+(\.\d+)?$', expression_string):
            return {'type': 'number', 'value': float(expression_string)}

        return {'type': 'unknown'} # Could not parse known simple type


    def _render_simple_bar(self, ax, y_pos, name, value, definition, question_data, all_vars_values, max_x):
        """Renders a standard single bar with enhancements for simple operations."""
        parsed_def = self._parse_simple_expression(definition, all_vars_values)
        label_text = f"{name}: {value:.1f}"
        is_unknown = name in question_data.get('unknowns', [])
        bar_alpha = 0.8

        # Case 1: Addition (A = B + C) -> Show B and C segments adding up to A
        if parsed_def['type'] == 'add':
            base_val = parsed_def['base_val']
            diff_val = parsed_def['diff_val']
            base_var = parsed_def['base_var']
            base_color = self._get_color_for_variable(base_var, alpha=bar_alpha)
            diff_color = self._get_color_for_variable(f"diff_{base_var}", alpha=bar_alpha/1.5) # Slightly different color for diff

            # Draw base segment (B)
            ax.barh(y_pos, base_val, height=0.6, color=base_color, edgecolor='black')
            self._add_dimension_line(ax, 0, base_val, y_pos, f"{base_var} ({base_val:.0f})")

            # Draw difference segment (C)
            ax.barh(y_pos, diff_val, left=base_val, height=0.6, color=diff_color, edgecolor='black', hatch='///', facecolor=diff_color) # Use facecolor with hatch
            self._add_dimension_line(ax, base_val, base_val + diff_val, y_pos, f"+ {diff_val:.0f}")

            # Add total dimension line for A
            self._add_dimension_line(ax, 0, value, y_pos, f"Total {name} ({value:.0f})", offset=0.8)

        # Case 2: Subtraction (A = B - C) -> Show B total, with segment A and segment C (difference)
        elif parsed_def['type'] == 'subtract':
            base_val = parsed_def['base_val'] # This is B (the whole)
            diff_val = parsed_def['diff_val'] # This is C (the part subtracted)
            result_val = value             # This is A (the remaining part)
            base_var = parsed_def['base_var']
            result_color = self._get_color_for_variable(name, alpha=bar_alpha) # Color for the result A
            diff_color = self._get_color_for_variable(f"diff_{base_var}", alpha=bar_alpha/1.5)

            # Draw the resulting part (A)
            ax.barh(y_pos, result_val, height=0.6, color=result_color, edgecolor='black')
            self._add_dimension_line(ax, 0, result_val, y_pos, f"{name} ({result_val:.0f})")

            # Draw the subtracted part (C) - hatched
            ax.barh(y_pos, diff_val, left=result_val, height=0.6, color='none', edgecolor=self.hatch_color, hatch='xxx')
            # Optional: Add a light background color for the subtracted part?
            # ax.barh(y_pos, diff_val, left=result_val, height=0.6, color=diff_color, alpha=0.2, edgecolor=self.hatch_color)
            self._add_dimension_line(ax, result_val, result_val + diff_val, y_pos, f"Removed ({diff_val:.0f})")

            # Add dimension line for the original whole (B)
            self._add_dimension_line(ax, 0, base_val, y_pos, f"Original {base_var} ({base_val:.0f})", offset=0.8)

        # Case 3: Division/Multiplication/Reference/Number -> Show single bar for the value A
        else:
            bar_color = self._get_color_for_variable(name, alpha=bar_alpha)
            ax.barh(y_pos, value, height=0.6, color=bar_color, edgecolor='black')
            # Add a single dimension line for the total value
            self._add_dimension_line(ax, 0, value, y_pos, f"{name} ({value:.0f})")

        # Add leader label for all simple bars
        self._add_leader_label(ax, value, y_pos, label_text, value, max_x)

        # Add equation if it's an unknown
        if is_unknown and definition:
             self._add_equation(ax, y_pos, definition, value, name)


    def _render_composite_bar(self, ax, y_pos, name, value, definition, question_data, all_vars_values, max_x):
        """Renders a segmented bar for composite variables with technical drawing style."""
        segments = self._parse_composite_expression(definition, all_vars_values)
        is_unknown = name in question_data.get('unknowns', [])
        bar_alpha = 0.8

        current_left = 0
        segment_boundaries = [0]

        for segment in segments:
            segment_color = self._get_color_for_variable(segment['variable'], alpha=bar_alpha)
            ax.barh(y_pos, segment['term_value'], left=current_left, height=0.6,
                    color=segment_color, edgecolor='black')

            # Add dimension line for this segment
            label = f"{int(segment['coefficient'])} x {segment['variable']}" if segment['coefficient'] != 1 else segment['variable']
            self._add_dimension_line(ax, current_left, current_left + segment['term_value'], y_pos, f"{label} ({segment['term_value']:.0f})")

            current_left += segment['term_value']
            segment_boundaries.append(current_left)

        # Add total dimension line spanning all segments
        self._add_dimension_line(ax, 0, value, y_pos, f"Total {name} ({value:.0f})", offset=0.8)

        # Add leader label for the total
        label_text = f"{name}: {value:.1f}"
        self._add_leader_label(ax, value, y_pos, label_text, value, max_x)

        # Add equation if it's an unknown (usually true for composite)
        if is_unknown:
             self._add_equation(ax, y_pos, definition, value, name)

    def _parse_composite_expression(self, expression_string, all_vars_values):
        """Parses expressions like '2*varA + 3*varB + varC'."""
        # Use findall to get all terms separated by '+'
        raw_terms = [t.strip() for t in expression_string.split('+')]

        term_details = []
        for term in raw_terms:
            # Try matching 'coeff * var' format
            match_coeff_var = re.match(r'(\d+(?:\.\d+)?)\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)$', term)
            # Try matching 'var' format
            match_var_only = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)$', term)

            if match_coeff_var:
                coefficient = float(match_coeff_var.group(1))
                variable_name = match_coeff_var.group(2)
            elif match_var_only:
                coefficient = 1.0
                variable_name = match_var_only.group(1)
            else:
                logger.warning(f"Could not parse term '{term}' in expression: {expression_string}")
                continue # Skip malformed terms

            if variable_name not in all_vars_values:
                raise ValueError(f"Variable '{variable_name}' used in composite expression '{expression_string}' not found in calculated values: {all_vars_values.keys()}")

            base_value = all_vars_values[variable_name]
            term_value = coefficient * base_value

            term_details.append({
                'variable': variable_name,
                'coefficient': coefficient,
                'base_value': base_value,
                'term_value': term_value,
                'label': f"{coefficient}*{variable_name}" if coefficient != 1 else variable_name
            })
        return term_details

    def _is_composite_sum_of_products(self, expression_string):
        """Checks if the expression is a sum of potentially multiplied terms."""
        if '+' not in expression_string:
            return False
        # Check if terms look like variables or coeff*variable
        terms = [t.strip() for t in expression_string.split('+')]
        if len(terms) < 2: return False # Need at least two terms for a sum

        # Relaxed check: allows simple variables or coeff*variable
        valid_term = re.compile(r'^(?:(?:\d+(?:\.\d+)?\s*\*\s*)?[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)$')

        if all(valid_term.match(term) for term in terms):
            # Final check: Ensure it's not just Var + Number (handled by simple)
            is_simple_add = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\+\s*\d+(?:\.\d+)?$', expression_string) or \
                            re.match(r'^\d+(?:\.\d+)?\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*$', expression_string)
            return not is_simple_add
        return False

    def render(self, bar_model, question_data):
        """Render the bar model using appropriate visualization styles in reverse order."""
        self._reset_colors() # Reset colors for the new question

        all_calculated_values = bar_model.weights
        variable_definitions = question_data['variables']

        # Identify all variables to plot (both simple and composite)
        items_to_plot = []
        max_val = 0
        vars_in_composites = set() # Keep track of base vars used in composites

        # First pass: Identify composites and their components (keep this for reference)
        for name, definition in variable_definitions.items():
            if name not in all_calculated_values: continue
            if self._is_composite_sum_of_products(definition):
                try: # Add error handling in case parsing fails
                    parsed_segments = self._parse_composite_expression(definition, all_calculated_values)
                    for seg in parsed_segments:
                        vars_in_composites.add(seg['variable'])
                except ValueError as e:
                    logger.error(f"Error parsing composite expression for {name}: {e}")

        # Second pass: SIMPLIFIED LOGIC - Plot all calculated variables
        items_to_plot = []
        max_val = 0
        
        for name, value in all_calculated_values.items():
            # Ensure the variable has a definition entry
            if name not in variable_definitions:
                logger.warning(f"Variable '{name}' found in calculated values but not in definitions. Skipping.")
                continue

            definition = variable_definitions[name]
            max_val = max(max_val, value)
            plot_item = {'name': name, 'value': value, 'definition': definition}

            # Determine plot type based on definition
            if self._is_composite_sum_of_products(definition):
                plot_item['type'] = 'composite'
            else:
                plot_item['type'] = 'simple' # Includes inputs, intermediate calculations, simple unknowns

            items_to_plot.append(plot_item) # Add ALL variables to the plot list

        # Determine plot height dynamically
        num_items = len(items_to_plot)
        # Estimate height: Base + space per bar (more space needed for annotations)
        plot_height = 3 + num_items * 2.5 # Generous spacing for annotations/equations
        plot_width = 12

        fig, (text_ax, main_ax) = plt.subplots(2, 1, figsize=(plot_width, plot_height),
                                               gridspec_kw={'height_ratios': [1, 10]})

        text_ax.text(0.0, 0.95, question_data['question'], fontsize=12, ha='left', va='top', wrap=True)
        text_ax.axis('off')

        main_ax.set_title("Bar Model Visualization")
        main_ax.set_xlim(0, max_val * 1.25) # Add more space for labels on the right
        main_ax.set_ylim(0, num_items * 2.5) # Set Y limit based on number of items & spacing

        # Plotting in reverse order (bottom-up)
        current_y_base = 1.0 # Start plotting near the bottom

        # Sort items perhaps by value or keep definition order? Let's keep definition order for now.
        # To reverse, we iterate through items_to_plot normally but assign increasing y values.

        for item in items_to_plot:
            name = item['name']
            value = item['value']
            definition = item['definition']
            plot_type = item['type']

            if plot_type == 'simple':
                self._render_simple_bar(main_ax, current_y_base, name, value, definition, question_data, all_calculated_values, max_val)
            elif plot_type == 'composite':
                 self._render_composite_bar(main_ax, current_y_base, name, value, definition, question_data, all_calculated_values, max_val)

            current_y_base += 2.5 # Move up for the next bar (increase y)

        # Finalize plot appearance
        main_ax.set_yticks([]) # No Y-axis ticks needed
        main_ax.spines['top'].set_visible(False)
        main_ax.spines['right'].set_visible(False)
        main_ax.spines['left'].set_visible(False)
        # main_ax.invert_yaxis() # NO longer needed as we plot bottom-up

        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.subplots_adjust(hspace=0.1) # Reduce space between text and plot if needed

        plt.show()