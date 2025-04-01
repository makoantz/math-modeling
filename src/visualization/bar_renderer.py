import matplotlib.pyplot as plt
import numpy as np
import logging
import io

logger = logging.getLogger(__name__)

class BarRenderer:
    def __init__(self):
        """Initialize the renderer with color settings."""
        # Define a color palette for variables
        self.colors = [
            "#3498db",  # Blue
            "#e74c3c",  # Red
            "#2ecc71",  # Green
            "#f39c12",  # Orange
            "#9b59b6",  # Purple
            "#1abc9c",  # Teal
            "#d35400",  # Dark Orange
            "#34495e",  # Dark Blue
            "#7f8c8d",  # Gray
            "#2c3e50",  # Navy
        ]
        self.color_index = 0
        self.var_colors = {}  # Dictionary to store assigned colors

    def _reset_colors(self):
        """Reset the color assignment."""
        self.color_index = 0
        self.var_colors = {}

    def _get_color_for_variable(self, var_name, alpha=1.0):
        """Get a consistent color for a variable, returning a format Matplotlib understands."""
        if var_name not in self.var_colors:
            self.var_colors[var_name] = self.colors[self.color_index % len(self.colors)]
            self.color_index += 1

        hex_color = self.var_colors[var_name]

        # Convert hex to RGB tuple (floats 0-1)
        h = hex_color.lstrip('#')
        # Ensure length is 6 before trying to unpack
        if len(h) == 6:
             rgb_float = tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        else:
             # Handle potential invalid hex color gracefully (e.g., return default gray)
             logger.warning(f"Invalid hex color format encountered: {hex_color}. Using gray.")
             rgb_float = (0.5, 0.5, 0.5) # Gray

        # Return RGBA tuple
        return (*rgb_float, alpha) # Use tuple packing

    def _add_dimension_line(self, ax, x_start, x_end, y_base, label_text, offset=0.4):
        """Add a measurement/dimension line above a bar segment."""
        y_line = y_base + offset
        
        # Draw the horizontal line
        ax.plot([x_start, x_end], [y_line, y_line], 'k-', linewidth=0.75)
        
        # Draw vertical ticks at ends
        tick_height = 0.1
        ax.plot([x_start, x_start], [y_line, y_line + tick_height], 'k-', linewidth=0.75)
        ax.plot([x_end, x_end], [y_line, y_line + tick_height], 'k-', linewidth=0.75)
        
        # Add label
        midpoint = (x_start + x_end) / 2
        ax.text(midpoint, y_line + tick_height + 0.05, label_text, ha='center', va='bottom', fontsize=8)

    def _add_leader_label(self, ax, x_pos, y_pos, label_text, value, max_x):
        """Add a leader label at the end of a bar."""
        padding = max_x * 0.01  # Small padding for text positioning
        # Calculate label position (ensure it doesn't go outside the plot)
        label_x = min(x_pos + padding, max_x * 0.95)
        
        # Add the label
        text = f"{label_text}: {value:.1f}"
        ax.text(label_x, y_pos, text, fontsize=9, va='center')
        
        # Draw leader line (if space permits)
        if padding > 0:
            ax.plot([x_pos, label_x - padding/2], [y_pos, y_pos], 'k-', linewidth=0.5)

    def _parse_simple_expression(self, expression):
        """Parse a simple expression into a variable."""
        return expression.strip()

    def _parse_composite_expression(self, expression, values):
        """Parse a composite expression (sum of products) into segments."""
        segments = []
        
        # Split by + to get terms
        parts = expression.split('+')
        for part in parts:
            part = part.strip()
            
            # Check if it's a product (contains *) or a single variable
            if '*' in part:
                factor_parts = part.split('*')
                variable = factor_parts[-1].strip()  # Last part is the variable
                
                # Calculate coefficient (product of numeric factors)
                coefficient = 1.0
                for i in range(len(factor_parts) - 1):
                    try:
                        coefficient *= float(factor_parts[i].strip())
                    except ValueError:
                        # If the factor is a variable, use its value
                        var_name = factor_parts[i].strip()
                        if var_name in values:
                            coefficient *= float(values[var_name])
                        else:
                            raise ValueError(f"Unknown variable: {var_name}")
                
                segments.append({
                    'variable': variable,
                    'coefficient': coefficient,
                    'value': coefficient * float(values[variable]) if variable in values else None
                })
            else:
                # Single variable
                variable = part
                segments.append({
                    'variable': variable,
                    'coefficient': 1.0,
                    'value': float(values[variable]) if variable in values else None
                })
                
        return segments

    def _is_composite_sum_of_products(self, expression):
        """Check if an expression is a composite sum of products."""
        return '+' in expression or '*' in expression

    def _render_simple_bar(self, ax, y_base, name, value, definition, question_data, all_values, max_val):
        """Render a simple bar (single variable)."""
        variable = self._parse_simple_expression(definition)
        color = self._get_color_for_variable(variable)
        
        # Draw the bar
        bar = ax.barh(y_base, value, height=0.8, left=0, color=color, edgecolor='black', linewidth=0.5)[0]
        
        # Add a label inside the bar if it's wide enough
        if value > max_val * 0.1:  # Only add label if the bar is at least 10% of max width
            ax.text(value/2, y_base, variable, ha='center', va='center', color='white', fontweight='bold', fontsize=9)
        
        # Add leader label
        self._add_leader_label(ax, value, y_base, name, value, max_val * 1.25)
        
        # Add dimension line
        self._add_dimension_line(ax, 0, value, y_base, f"{value:.1f}")

    def _render_composite_bar(self, ax, y_base, name, value, definition, question_data, all_values, max_val):
        """Render a composite bar (sum of products)."""
        try:
            segments = self._parse_composite_expression(definition, all_values)
            
            # Sort segments by variable for consistent coloring
            segments.sort(key=lambda x: x['variable'])
            
            # Draw segments
            left = 0
            annotation_offset = 0.4  # Base offset for first level of annotation
            
            for segment in segments:
                if segment['value'] is None:
                    continue
                
                seg_value = segment['value']
                variable = segment['variable']
                coefficient = segment['coefficient']
                
                # Skip segment if value is too small
                if seg_value < 0.001:
                    continue
                
                color = self._get_color_for_variable(variable)
                
                # Draw the segment
                bar = ax.barh(
                    y_base, seg_value, height=0.8, left=left, 
                    color=color, edgecolor='black', linewidth=0.5
                )[0]
                
                # Add a label inside the segment if it's wide enough
                if seg_value > max_val * 0.05:  # Only add if segment is at least 5% of max
                    if coefficient != 1.0:
                        label = f"{coefficient:.1f}×{variable}"
                    else:
                        label = variable
                    
                    ax.text(
                        left + seg_value/2, y_base, label,
                        ha='center', va='center', color='white', fontweight='bold', fontsize=8
                    )
                
                # Add dimension line for this segment
                self._add_dimension_line(
                    ax, left, left + seg_value, y_base, 
                    f"{coefficient:.1f}×{variable}={seg_value:.1f}",
                    offset=annotation_offset
                )
                
                left += seg_value
            
            # Add leader label for the entire bar
            self._add_leader_label(ax, value, y_base, name, value, max_val * 1.25)
            
            # Add total dimension line (level 2 annotation)
            self._add_dimension_line(
                ax, 0, value, y_base, f"Total: {value:.1f}",
                offset=annotation_offset + 0.4  # Higher offset for second level
            )
            
            # Add equation below the bar
            equation_text = " + ".join([
                f"{s['coefficient']:.1f}×{s['variable']}" if s['coefficient'] != 1.0 else s['variable']
                for s in segments if s['value'] is not None
            ]) + f" = {value:.1f}"
            
            # Place equation text at a lower position
            ax.text(
                0, y_base - 0.6, equation_text,
                ha='left', va='top', fontsize=8, style='italic', color='#555'
            )
            
        except Exception as e:
            logger.error(f"Error rendering composite bar: {e}")
            # Fallback to simple bar if composite parsing fails
            self._render_simple_bar(ax, y_base, name, value, definition, question_data, all_values, max_val)

    def render_to_buffer(self, bar_model, question_data):
        """Renders the bar model to an in-memory PNG buffer."""
        self._reset_colors()

        all_calculated_values = bar_model.weights
        variable_definitions = question_data['variables']

        # Logic to determine items to plot and max value
        items_to_plot = []
        max_val = 0
        vars_in_composites = set()

        for name, definition in variable_definitions.items():
            if name not in all_calculated_values: continue
            if self._is_composite_sum_of_products(definition):
                try:
                    parsed_segments = self._parse_composite_expression(definition, all_calculated_values)
                    for seg in parsed_segments: 
                        vars_in_composites.add(seg['variable'])
                except Exception as e: 
                    logger.error(f"Parse error: {e}")

        for name, value in all_calculated_values.items():
             if name not in variable_definitions: continue
             # Ensure value is float before comparison/calculation
             try:
                 f_value = float(value)
             except (ValueError, TypeError):
                 logger.warning(f"Skipping variable '{name}' due to non-numeric value: {value}")
                 continue # Skip this item if value isn't numeric
                 
             definition = variable_definitions[name]
             max_val = max(max_val, f_value)
             plot_item = {'name': name, 'value': f_value, 'definition': definition}
             if self._is_composite_sum_of_products(definition):
                 plot_item['type'] = 'composite'
             else:
                 plot_item['type'] = 'simple'
             items_to_plot.append(plot_item)
        
        # Ensure max_val is at least 1 to prevent issues if all values are 0
        max_val = max(max_val, 1.0)

        # Sort items by name for consistency
        items_to_plot.sort(key=lambda x: x['name'])
        
        # Determine plot dimensions dynamically
        num_items = len(items_to_plot)
        # Make figure height proportional to the number of items
        plot_height_inches = 2.0 + num_items * 1.5  
        # Make width wider to accommodate labels
        plot_width_inches = 12

        # Create Figure and Axes with more space
        plt.rcParams.update({'figure.autolayout': True})
        fig, main_ax = plt.subplots(figsize=(plot_width_inches, plot_height_inches))

        # REMOVED: Problem statement from figure (shown in HTML already)
        # Add only the title
        main_ax.set_title("Bar Model Visualization", pad=15)
        
        # Set axis limits with extra space
        main_ax.set_xlim(0, max_val * 1.3)  # Extra space for labels
        main_ax.set_ylim(-0.5, num_items * 3.0)  # Start below zero for extra space
        
        # Add grid for better readability
        main_ax.grid(axis='x', linestyle='--', alpha=0.3)

        # Plotting loop
        current_y_base = 1.5  # Start higher for spacing
        
        for item in items_to_plot:
            name = item['name']
            value = item['value']
            definition = item['definition']
            plot_type = item['type']

            if plot_type == 'simple':
                self._render_simple_bar(main_ax, current_y_base, name, value, definition, 
                                        question_data, all_calculated_values, max_val)
            elif plot_type == 'composite':
                self._render_composite_bar(main_ax, current_y_base, name, value, definition, 
                                          question_data, all_calculated_values, max_val)

            current_y_base += 3.0  # Increase spacing between bars

        # Finalize plot appearance
        main_ax.set_yticks([])
        main_ax.spines['top'].set_visible(False)
        main_ax.spines['right'].set_visible(False)
        main_ax.spines['left'].set_visible(False)
        
        # Configure layout with extra room - critical for preventing cropping
        plt.tight_layout(pad=2.5)
        
        # Save to buffer with IMPORTANT settings to prevent cropping
        buf = io.BytesIO()
        fig.savefig(
            buf, 
            format='png', 
            dpi=120,  # Higher DPI for better quality
            bbox_inches='tight',  # Ensure all elements are captured
            pad_inches=0.75  # Add significant padding around the entire figure
        )
        buf.seek(0)

        # Close the figure to release memory
        plt.close(fig)

        return buf

    def render(self, bar_model, question_data):
        """Render the bar model using Matplotlib and display it."""
        # Create the visualization
        buffer = self.render_to_buffer(bar_model, question_data)
        
        # Display the figure
        plt.figure()
        plt.imshow(plt.imread(buffer))
        plt.axis('off')
        plt.tight_layout()
        plt.show()