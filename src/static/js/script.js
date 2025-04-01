// Global variable to store questions of the currently loaded set
window.currentQuestions = [];
const API_BASE_URL = ""; // Assuming Flask serves from the root

// DOM Elements
const questionSetSelect = document.getElementById('question-set-select');
const questionSelect = document.getElementById('question-select');
const questionTextDisplay = document.getElementById('question-text-display');
const visualizationArea = document.getElementById('visualization-area');
const errorDisplay = document.getElementById('error-display');
const resetViewBtn = document.getElementById('reset-view-btn');
const zoomInBtn = document.getElementById('zoom-in-btn');
const zoomOutBtn = document.getElementById('zoom-out-btn');
const zoomScaleDisplay = document.getElementById('zoom-scale');

// Add global variable to track panzoom instance
let currentPanzoomInstance = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed.");
    // Add event listeners
    questionSetSelect.addEventListener('change', handleQuestionSetChange);
    questionSelect.addEventListener('change', handleQuestionSelectionChange);
    resetViewBtn.addEventListener('click', resetPanzoomView);
    
    // Add zoom button event listeners
    if (zoomInBtn) zoomInBtn.addEventListener('click', zoomIn);
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', zoomOut);

    // Initial load
    fetchQuestionSets();
});

// Zoom control functions
function zoomIn() {
    if (currentPanzoomInstance) {
        currentPanzoomInstance.zoomIn();
        updateZoomDisplay();
    }
}

function zoomOut() {
    if (currentPanzoomInstance) {
        currentPanzoomInstance.zoomOut();
        updateZoomDisplay();
    }
}

function updateZoomDisplay() {
    if (currentPanzoomInstance && zoomScaleDisplay) {
        const scale = Math.round(currentPanzoomInstance.getScale() * 100);
        zoomScaleDisplay.textContent = `${scale}%`;
    }
}

// Reset panzoom view to initial state
function resetPanzoomView() {
    if (currentPanzoomInstance) {
        currentPanzoomInstance.reset();
        updateZoomDisplay();
    }
}

// --- Event Handlers ---
function handleQuestionSetChange(event) {
    const selectedFilename = event.target.value;
    if (selectedFilename) {
        console.log(`Question set selected: ${selectedFilename}`);
        loadQuestionSet(selectedFilename);
    }
}

function handleQuestionSelectionChange(event) {
    const selectedIndex = event.target.value;
    if (selectedIndex !== "" && selectedIndex !== null) {
        console.log(`Question index selected: ${selectedIndex}`);
        displayQuestion(parseInt(selectedIndex, 10));
    }
}

// --- API Fetching Functions ---

async function fetchQuestionSets() {
    console.log("Fetching question sets...");
    clearError();
    try {
        const response = await fetch(`${API_BASE_URL}/api/question-sets`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Received question sets:", data);

        // Clear previous options
        questionSetSelect.innerHTML = '<option value="">-- Select Set --</option>';
        questionSelect.innerHTML = '<option value="">-- Select Question --</option>'; // Reset questions too

        if (data && data.length > 0) {
            data.forEach(filename => {
                const option = document.createElement('option');
                option.value = filename;
                option.textContent = filename;
                questionSetSelect.appendChild(option);
            });
            // Automatically load the first set
            questionSetSelect.value = data[0]; // Select it in the dropdown
            loadQuestionSet(data[0]); // Load its questions
        } else {
            showError("No question sets found in the data folder.");
        }
    } catch (error) {
        console.error('Error loading question sets:', error);
        showError('Error loading question sets: ' + error.message);
    }
}

async function loadQuestionSet(filename) {
    console.log(`Loading question set: ${filename}`);
    clearError();
    clearVisualization(); // Clear old viz
    questionTextDisplay.textContent = "Loading questions..."; // Update status
    try {
        const response = await fetch(`${API_BASE_URL}/api/question-set/${filename}`);
         if (!response.ok) {
             const errorData = await response.json().catch(() => ({ error: `HTTP error! status: ${response.status}` }));
             throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
         }
        const data = await response.json();
        console.log("Received questions data:", data);

        // Update UI with questions
        questionSelect.innerHTML = '<option value="">-- Select Question --</option>'; // Clear previous

        if (data && data.questions && data.questions.length > 0) {
            window.currentQuestions = data.questions; // Store questions data
            data.questions.forEach((question, index) => {
                const option = document.createElement('option');
                option.value = index;
                // Shorten long question text for the dropdown
                const shortText = question.question.length > 80 ? question.question.substring(0, 80) + "..." : question.question;
                option.textContent = `Q ${index + 1}: ${shortText}`;
                questionSelect.appendChild(option);
            });

            // Automatically display the first question
            questionSelect.value = 0; // Select it
            displayQuestion(0); // Display it
        } else {
            window.currentQuestions = []; // Clear stored data
            showError("No questions found in this set.");
            questionTextDisplay.textContent = "No questions found in this set.";
        }
    } catch (error) {
        console.error('Error loading question set:', error);
        showError(`Error loading ${filename}: ${error.message}`);
        questionTextDisplay.textContent = `Failed to load questions from ${filename}.`;
    }
}

async function solveAndVisualize(questionIndex) {
    console.log(`Solving question index ${questionIndex} and requesting image...`);
    
    // Destroy previous Panzoom instance if it exists
    if (currentPanzoomInstance) {
        console.log("Destroying previous Panzoom instance.");
        currentPanzoomInstance.destroy();
        currentPanzoomInstance = null;
    }
    
    if (questionIndex < 0 || questionIndex >= window.currentQuestions.length) {
        showError("Invalid question index.");
        return;
    }
    clearError();
    clearVisualization(); // Clear previous image/message
    const questionData = window.currentQuestions[questionIndex];
    questionTextDisplay.textContent = `Solving: ${questionData.question}`;

    try {
        // Step 1: Solve the problem
        console.log("Calling /api/solve");
        const solveResponse = await fetch(`${API_BASE_URL}/api/solve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_data: questionData })
        });
        if (!solveResponse.ok) {
            const errorData = await solveResponse.json().catch(() => ({ error: `Solve request failed! status: ${solveResponse.status}` }));
            throw new Error(`Solve Error: ${errorData.error || `HTTP status ${solveResponse.status}`}`);
        }
        const solveResult = await solveResponse.json();
        console.log("Solve successful:", solveResult);

        // Step 2: Display the visualization image
        console.log("Requesting visualization image from /api/visualize");
        
        // Create image element
        const img = document.createElement('img');
        img.alt = `Bar model visualization for question ${questionIndex + 1}`;
        
        // Add loading indicator
        visualizationArea.innerHTML = '<div class="loading">Generating visualization...</div>';

        // Request the image
        const vizResponse = await fetch(`${API_BASE_URL}/api/visualize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_data: questionData, results: solveResult.results })
        });

        if (!vizResponse.ok) {
            const errorData = await vizResponse.json().catch(() => ({ error: `Viz request failed! status: ${vizResponse.status}` }));
            throw new Error(`Visualization Error: ${errorData.error || `HTTP status ${vizResponse.status}`}`);
        }

        const imageBlob = await vizResponse.blob(); // Get image data as a Blob
        const imageUrl = URL.createObjectURL(imageBlob); // Create a temporary URL for the Blob
        img.src = imageUrl;
        
        // Clear loading indicator and add image
        visualizationArea.innerHTML = '';
        
        // Recreate zoom controls (they were cleared by innerHTML)
        if (visualizationArea) {
            // Only recreate if not already in the HTML
            if (!document.getElementById('zoom-in-btn')) {
                const zoomControls = document.createElement('div');
                zoomControls.className = 'zoom-controls';
                zoomControls.innerHTML = `
                    <button id="zoom-in-btn" class="zoom-button">+</button>
                    <button id="zoom-out-btn" class="zoom-button">−</button>
                `;
                visualizationArea.appendChild(zoomControls);
                
                // Re-add event listeners
                document.getElementById('zoom-in-btn').addEventListener('click', zoomIn);
                document.getElementById('zoom-out-btn').addEventListener('click', zoomOut);
            }
            
            // Recreate scale display if needed
            if (!document.getElementById('zoom-scale')) {
                const scaleDisplay = document.createElement('div');
                scaleDisplay.id = 'zoom-scale';
                scaleDisplay.className = 'zoom-scale';
                scaleDisplay.textContent = '90%'; // Initial scale
                visualizationArea.appendChild(scaleDisplay);
            }
        }
        
        visualizationArea.appendChild(img);
        
        // Initialize Panzoom when image is loaded
        img.onload = () => {
            URL.revokeObjectURL(imageUrl); // Free memory
            
            // Initialize Panzoom
            try {
                currentPanzoomInstance = Panzoom(img, {
                    maxScale: 5,         // Allow zooming up to 5x
                    minScale: 0.5,       // Allow zooming out to 0.5x
                    contain: 'outside',  // Keep image within bounds mostly
                    startScale: 0.9,     // Start slightly zoomed out to show full image
                    cursor: 'grab',      // Show grab cursor
                    
                    // Adjust startY to move content down more (keep startX at 0 for horizontal centering)
                    startX: 0,           // Center horizontally
                    startY: 0,         // Positive = shift down (increased from 50 to 150)
                    
                    // Generous overflow to allow freedom of movement
                    overflow: {
                        top: 400,        // Increased to allow more movement upward
                        left: 300,
                        right: 300,
                        bottom: 200
                    },
                    // Ensure panning is enabled
                    panOnlyWhenZoomed: false,
                    disablePan: false,
                    animate: true
                });
                
                // Add wheel zoom listener
                visualizationArea.addEventListener('wheel', handleWheelZoom);
                
                // Update zoom display
                updateZoomDisplay();

                console.log("Panzoom initialized successfully");
            } catch (panzoomError) {
                console.error("Failed to initialize Panzoom:", panzoomError);
            }
        };
        
        img.onerror = () => { 
            URL.revokeObjectURL(imageUrl); 
            showError('Failed to load visualization image.'); 
        };

        // Update question text display
        questionTextDisplay.textContent = questionData.question;

    } catch (error) {
        console.error('Error during solve/visualize process:', error);
        showError(`Processing Error: ${error.message}`);
        questionTextDisplay.textContent = questionData.question; // Reset text on error
    }
}

// Handle wheel zoom with scale update
function handleWheelZoom(event) {
    if (currentPanzoomInstance) {
        event.preventDefault();
        currentPanzoomInstance.zoomWithWheel(event);
        updateZoomDisplay();
    }
}

// --- UI Update Functions ---

function displayQuestion(index) {
    if (index >= 0 && index < window.currentQuestions.length) {
        const question = window.currentQuestions[index];
        console.log(`Displaying question ${index}: ${question.question}`);
        questionTextDisplay.textContent = question.question; // Display full text
        // Trigger the solving and visualization process
        solveAndVisualize(index);
    } else {
        questionTextDisplay.textContent = "Please select a valid question.";
        clearVisualization();
    }
}

function showError(message) {
    errorDisplay.textContent = message;
    errorDisplay.style.display = 'block'; // Make it visible
}

function clearError() {
    errorDisplay.textContent = '';
    errorDisplay.style.display = 'none'; // Hide it
}

function clearVisualization() {
    visualizationArea.innerHTML = ''; // Clear the drawing area
    
    // Destroy panzoom instance if it exists
    if (currentPanzoomInstance) {
        console.log("Clearing visualization, destroying Panzoom instance.");
        // Remove wheel event listener to prevent memory leaks
        visualizationArea.removeEventListener('wheel', handleWheelZoom);
        currentPanzoomInstance.destroy();
        currentPanzoomInstance = null;
    }
}