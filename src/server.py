from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# --- Import your backend logic ---
# Assumes backend_controller.py and visual_data_generator.py are in the same directory or accessible via Python path
try:
    from backend_controller import load_questions_from_file, solve_problem
    from visualization.visual_data_generator import generate_visualization_data # Need to create this file
except ImportError as e:
    logging.error(f"Failed to import backend modules: {e}")
    # Optionally exit or raise a more specific error if these are critical
    raise

# --- Configuration ---
# Correctly calculate paths relative to this file's location (src/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, '..', 'data') # Go up one level to project root, then into data
STATIC_FOLDER = os.path.join(BASE_DIR, 'static') # Static folder inside src/

# Create Flask app first
# Define static folder and URL path correctly
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
CORS(app)  # Allow all origins for development simplicity

# Setup logging AFTER creating app
log_dir = os.path.join(BASE_DIR, 'logs') # Logs directory inside src/
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'server.log')

# Configure logging format and handler
log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
log_handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=3) # Increased maxBytes
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO) # Log INFO level and above

# Clear existing handlers if any (useful during development/reloads)
if app.logger.hasHandlers():
    app.logger.handlers.clear()

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Math Modeling server startup')

# --- API Endpoints ---

@app.route('/api/question-sets', methods=['GET'])
def get_question_sets():
    """Lists available JSON files in the data directory."""
    app.logger.info(f"Request received for /api/question-sets. Data folder: {DATA_FOLDER}")
    if not os.path.isdir(DATA_FOLDER):
        app.logger.error(f"Data folder not found at {DATA_FOLDER}")
        return jsonify({"error": "Data folder configured incorrectly."}), 500
    try:
        files = [f for f in os.listdir(DATA_FOLDER) if f.lower().endswith('.json')]
        app.logger.info(f"Found question sets: {files}")
        return jsonify(files)
    except Exception as e:
        app.logger.error(f"Error listing question sets: {e}", exc_info=True)
        return jsonify({"error": "Failed to list question sets."}), 500

@app.route('/api/question-set/<path:filename>', methods=['GET'])
def get_question_set_details(filename):
    """Loads and returns the content of a specific JSON file."""
    app.logger.info(f"Request received for /api/question-set/{filename}")
    # Basic security: prevent path traversal by ensuring the final path is within DATA_FOLDER
    file_path = os.path.abspath(os.path.join(DATA_FOLDER, filename))
    if not file_path.startswith(os.path.abspath(DATA_FOLDER)):
        app.logger.warning(f"Potential path traversal attempt blocked for filename: {filename}")
        return jsonify({"error": "Invalid filename"}), 400

    if not filename.lower().endswith('.json'):
         app.logger.warning(f"Request for non-JSON file blocked: {filename}")
         return jsonify({"error": "Invalid file type"}), 400

    try:
        data = load_questions_from_file(file_path) # Use your loading function
        app.logger.info(f"Successfully loaded data from {filename}")
        return jsonify(data)
    except FileNotFoundError:
        app.logger.error(f"Question set file not found: {file_path}")
        return jsonify({"error": "File not found"}), 404
    except json.JSONDecodeError:
         app.logger.error(f"Invalid JSON in file: {file_path}")
         return jsonify({"error": "Invalid JSON format in file"}), 500
    except Exception as e:
        app.logger.error(f"Error loading question set {filename}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to load question set: {e}"}), 500

@app.route('/api/solve', methods=['POST'])
def solve_question_api():
    """Solves a single question based on provided data."""
    app.logger.info("Request received for /api/solve")
    data = request.get_json()
    if not data or 'question_data' not in data:
        app.logger.warning("Solve request missing 'question_data'")
        return jsonify({"error": "Missing 'question_data' in request"}), 400

    question_content = data['question_data'].get('question', 'N/A')
    app.logger.info(f"Attempting to solve question: {question_content[:50]}...")

    try:
        results = solve_problem(data['question_data']) # Use your solver
        app.logger.info(f"Successfully solved question. Results: {results}")
        return jsonify({"results": results})
    except Exception as e:
        app.logger.error(f"Error solving question: {e}", exc_info=True)
        return jsonify({"error": f"Failed to solve: {e}"}), 500

@app.route('/api/visualization-data', methods=['POST'])
def get_visualization_data_api():
    """Generates structured data for frontend visualization."""
    app.logger.info("Request received for /api/visualization-data")
    data = request.get_json()
    if not data or 'question_data' not in data or 'results' not in data:
        app.logger.warning("Visualization data request missing 'question_data' or 'results'")
        return jsonify({"error": "Missing 'question_data' or 'results' in request"}), 400

    app.logger.info("Generating visualization data...")
    try:
        viz_data = generate_visualization_data(data['question_data'], data['results']) # Use the NEW generator
        app.logger.info("Successfully generated visualization data.")
        # app.logger.debug(f"Viz Data: {json.dumps(viz_data, indent=2)}") # Log data if needed (can be verbose)
        return jsonify(viz_data)
    except Exception as e:
        app.logger.error(f"Error generating visualization data: {e}", exc_info=True)
        return jsonify({"error": f"Failed to generate visualization: {e}"}), 500

# --- Route to serve the main HTML page ---
@app.route('/')
def index():
    """Serves the main index.html file."""
    app.logger.info("Request received for root '/', serving index.html")
    # Use send_from_directory for robustness
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
         app.logger.error(f"index.html not found in static folder: {app.static_folder}")
         return "Error: index.html not found.", 404


if __name__ == '__main__':
    app.logger.info('Starting Flask development server.')
    # Host 0.0.0.0 makes it accessible on the network, not just localhost
    # Use a specific port if needed, e.g., port=5001
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True enables auto-reload