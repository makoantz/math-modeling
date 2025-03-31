import re
import logging
import matplotlib.colors as mcolors  # Use matplotlib's color utilities
from model.bar_model import BarModel

logger = logging.getLogger(__name__)

# --- Color Management ---
# Use a known good colormap like tab10
_COLOR_MAP_BASE = list(mcolors.TABLEAU_COLORS.values())  # Get hex values from Tableau colors
_variable_color_map = {}
_color_index = 0
_hatch_color = '#888888'  # Color for hatching strokes
_dimension_color = '#333333'

def _reset_colors():
    global _variable_color_map, _color_index
    _variable_color_map = {}
    _color_index = 0
    logger.debug("Color map reset.")

def _get_color_for_variable(var_name):
    global _color_index
    # Assigns a consistent color hex code to each variable name.
    if var_name not in _variable_color_map:
        color = _COLOR_MAP_BASE[_color_index % len(_COLOR_MAP_BASE)]
        _variable_color_map[var_name] = color
        _color_index += 1
        logger.debug(f"Assigned color {color} to variable '{var_name}'")
    return _variable_color_map[var_name]

# --- Expression Parsing Logic (Adapted from bar_renderer.py) ---

def _parse_simple_expression(expression_string, all_vars_values):
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
    return {'type': 'unknown'}

def _parse_composite_expression(expression_string, all_vars_values):
    """Parses expressions like '2*varA + 3*varB + varC' into segment details."""
    segments = []
    raw_terms = [t.strip() for t in expression_string.split('+')]
    term_details = []
    for term in raw_terms:
        match_coeff_var = re.match(r'(\d+(?:\.\d+)?)\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)$', term)
        match_var_only = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)$', term)
        if match_coeff_var:
            coefficient = float(match_coeff_var.group(1))
            variable_name = match_coeff_var.group(2)
        elif match_var_only:
            coefficient = 1.0
            variable_name = match_var_only.group(1)
        else:
            logger.warning(f"Could not parse composite term '{term}' in: {expression_string}")
            continue
        if variable_name not in all_vars_values:
            raise ValueError(f"Variable '{variable_name}' in '{expression_string}' not found in calculated values.")
        base_value = all_vars_values[variable_name]
        term_value = coefficient * base_value
        term_details.append({
            'variable': variable_name,
            'coefficient': coefficient,
            'base_value': base_value,
            'term_value': term_value,
            # Color added later
            'label': f"{int(coefficient)} x {variable_name}" if coefficient != 1 else variable_name
        })
    return term_details

def _is_composite_sum_of_products(expression_string):
    """Checks if expression is composite sum, excluding simple 'var + num'."""
    if '+' not in expression_string: return False
    terms = [t.strip() for t in expression_string.split('+')]
    if len(terms) < 2: return False
    valid_term = re.compile(r'^(?:(?:\d+(?:\.\d+)?\s*\*\s*)?[a-zA-Z_][a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)$')
    if all(valid_term.match(term) for term in terms):
        is_simple_add = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\+\s*\d+(?:\.\d+)?$', expression_string) or \
                        re.match(r'^\d+(?:\.\d+)?\s*\+\s*[a-zA-Z_][a-zA-Z0-9_]*$', expression_string)
        return not is_simple_add
    return False

# --- Main Generator Function ---

def generate_visualization_data(question_data, results):
    """
    Generates a JSON-serializable dictionary describing the visualization.
    """
    logger.info("Generating detailed visualization data structure...")
    _reset_colors() # Reset colors for each new question generation

    output_bars = []
    max_value = 0
    all_variables = question_data.get("variables", {})
    unknowns = set(question_data.get("unknowns", []))

    # Sort results for consistent order (e.g., alphabetically) might be better
    # Let's sort by key for now to ensure consistency
    sorted_results_items = sorted(results.items())

    # Determine which variables to plot (all calculated for now)
    items_to_plot_names = [name for name, value in sorted_results_items if value is not None]

    # Calculate overall max_value first
    for name in items_to_plot_names:
        value = float(results[name])
        max_value = max(max_value, value)

    # Build data for each bar
    for name in items_to_plot_names:
        value = float(results[name])
        definition = all_variables.get(name, str(value))
        is_unknown = name in unknowns
        segments = []
        annotations = [] # For dimension lines/labels above bar
        bar_type = 'simple' # Default type

        # --- Determine bar type and structure segments/annotations ---
        if _is_composite_sum_of_products(definition):
            logger.debug(f"'{name}' is composite.")
            bar_type = "composite"
            parsed_segments = _parse_composite_expression(definition, results)
            current_offset = 0
            for seg_info in parsed_segments:
                term_val = seg_info['term_value']
                base_var = seg_info['variable']
                color = _get_color_for_variable(base_var)
                segments.append({
                    "value": term_val,
                    "label": f"{seg_info['label']} ({term_val:.0f})", # Annotation label
                    "color": color,
                    "hatch": False,
                    "base_var_ref": base_var
                })
                # Add segment annotation
                annotations.append({
                    "start_value": current_offset,
                    "end_value": current_offset + term_val,
                    "label": f"{seg_info['label']} ({term_val:.0f})",
                    "level": 1 # Level 1 for segment details
                })
                current_offset += term_val
            # Add total annotation for composite bar
            annotations.append({
                    "start_value": 0, "end_value": value,
                    "label": f"Total {name} ({value:.0f})", "level": 2 # Level 2 for overall total
                })

        else: # Handle simple types
            parsed_def = _parse_simple_expression(definition, results)
            bar_type = parsed_def.get('type', 'simple')
            logger.debug(f"'{name}' is simple, type: {bar_type}")

            if bar_type == 'add':
                base_val = parsed_def['base_val']
                diff_val = parsed_def['diff_val']
                base_var = parsed_def['base_var']
                base_color = _get_color_for_variable(base_var)
                diff_color = _get_color_for_variable(f"diff_{base_var}") # Consistent diff color

                segments.append({"value": base_val, "label": f"{base_var} ({base_val:.0f})", "color": base_color, "hatch": False, "base_var_ref": base_var})
                segments.append({"value": diff_val, "label": f"+ {diff_val:.0f}", "color": diff_color, "hatch": True, "hatch_pattern": "///"})

                annotations.append({"start_value": 0, "end_value": base_val, "label": f"{base_var} ({base_val:.0f})", "level": 1})
                annotations.append({"start_value": base_val, "end_value": value, "label": f"+ {diff_val:.0f}", "level": 1})
                annotations.append({"start_value": 0, "end_value": value, "label": f"Total {name} ({value:.0f})", "level": 2})

            elif bar_type == 'subtract':
                base_val = parsed_def['base_val'] # Original whole (B)
                diff_val = parsed_def['diff_val'] # Amount removed (C)
                result_val = value             # Remaining part (A = B - C)
                base_var = parsed_def['base_var']
                result_color = _get_color_for_variable(name) # Color for the result A
                # Use base var color for the 'whole' annotation
                diff_color = _get_color_for_variable(f"diff_{base_var}")

                # Segment for the result part A
                segments.append({"value": result_val, "label": f"{name} ({result_val:.0f})", "color": result_color, "hatch": False, "base_var_ref": name})
                # Segment placeholder for the removed part C (drawn with hatching)
                segments.append({"value": diff_val, "label": f"Removed ({diff_val:.0f})", "color": "transparent", "hatch": True, "hatch_pattern": "xxx"})

                # Annotations
                annotations.append({"start_value": 0, "end_value": result_val, "label": f"{name} ({result_val:.0f})", "level": 1})
                annotations.append({"start_value": result_val, "end_value": base_val, "label": f"Removed ({diff_val:.0f})", "level": 1})
                annotations.append({"start_value": 0, "end_value": base_val, "label": f"Original {base_var} ({base_val:.0f})", "level": 2})

            else: # Default simple (number, reference, multiply, divide)
                 color = _get_color_for_variable(name)
                 segments.append({"value": value, "label": f"{name} ({value:.0f})", "color": color, "hatch": False, "base_var_ref": name})
                 annotations.append({"start_value": 0, "end_value": value, "label": f"{name} ({value:.0f})", "level": 1})


        # --- Format Equation ---
        equation = ""
        if is_unknown:
            try:
                # Format definition nicely
                eq_str = definition
                for op in ['*', '+', '-', '/']:
                    eq_str = eq_str.replace(op, f" {op} ")
                equation = f"{name} = {eq_str.strip()} = {value:.1f}"
            except Exception: # Catch potential errors formatting complex strings
                 equation = f"{name} = {value:.1f} (Definition complex)"


        # --- Assemble bar data ---
        bar_data = {
            "name": name,
            "total_value": value,
            "type": bar_type,
            "definition": definition,
            "is_unknown": is_unknown,
            "segments": segments,
            "annotations": annotations,
            "equation": equation
        }
        output_bars.append(bar_data)

    # Ensure bottom-up order if needed (JS can also handle order)
    # output_bars.reverse() # If JS expects index 0 = bottom bar

    logger.info(f"Generated detailed data for {len(output_bars)} bars. Max value: {max_value}")
    return {"bars": output_bars, "max_value": max_value, "question_text": question_data.get('question','')}