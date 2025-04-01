# Must be at the very top before any matplotlib-related imports
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend for server environments

from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# --- Import your backend logic ---
try:
    from backend_controller import load_questions_from_file, solve_problem
    from visualization.bar_renderer import BarRenderer  # Import the Matplotlib renderer
    from model.bar_model import BarModel  # FIX: Correct import path for BarModel
except ImportError as e:
    logging.error(f"Failed to import backend modules: {e}")
    raise

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, '..', 'data')
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
CORS(app)

# Setup logging
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'server.log')

log_formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
log_handler = RotatingFileHandler(log_file, maxBytes=100000, backupCount=3)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(logging.INFO)

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
    file_path = os.path.abspath(os.path.join(DATA_FOLDER, filename))
    if not file_path.startswith(os.path.abspath(DATA_FOLDER)):
        app.logger.warning(f"Potential path traversal attempt blocked for filename: {filename}")
        return jsonify({"error": "Invalid filename"}), 400

    if not filename.lower().endswith('.json'):
         app.logger.warning(f"Request for non-JSON file blocked: {filename}")
         return jsonify({"error": "Invalid file type"}), 400

    try:
        data = load_questions_from_file(file_path)
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
        results = solve_problem(data['question_data'])
        app.logger.info(f"Successfully solved question. Results: {results}")
        return jsonify({"results": results})
    except Exception as e:
        app.logger.error(f"Error solving question: {e}", exc_info=True)
        return jsonify({"error": f"Failed to solve: {e}"}), 500

# --- NEW ENDPOINT: Generate and return visualization image ---
@app.route('/api/visualize', methods=['POST'])
def get_visualization_image():
    """Generates and returns the visualization as a PNG image."""
    app.logger.info("Request received for /api/visualize")
    data = request.get_json()
    if not data or 'question_data' not in data or 'results' not in data:
        app.logger.warning("Visualize request missing 'question_data' or 'results'")
        return jsonify({"error": "Missing 'question_data' or 'results' in request"}), 400

    question_data = data['question_data']
    results = data['results']
    question_text = question_data.get('question', 'N/A')

    app.logger.info(f"Generating visualization image for: {question_text[:50]}...")
    try:
        # Create a BarModel instance from the results
        bar_model = BarModel(results)
        renderer = BarRenderer()

        # Generate image buffer using the modified renderer method
        image_buffer = renderer.render_to_buffer(bar_model, question_data)

        app.logger.info("Successfully generated visualization image.")
        return send_file(
            image_buffer,
            mimetype='image/png',
            as_attachment=False  # Display inline
        )

    except Exception as e:
        app.logger.error(f"Error generating visualization image: {e}", exc_info=True)
        return jsonify({"error": f"Failed to generate visualization image: {e}"}), 500

# --- Route to serve the main HTML page ---
@app.route('/')
def index():
    """Serves the main index.html file."""
    app.logger.info("Request received for root '/', serving index.html")
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except FileNotFoundError:
         app.logger.error(f"index.html not found in static folder: {app.static_folder}")
         return "Error: index.html not found.", 404

if __name__ == '__main__':
    app.logger.info('Starting Flask development server.')
    app.run(host='0.0.0.0', port=5000, debug=True)