// Global variable to store questions of the currently loaded set
window.currentQuestions = [];
const API_BASE_URL = ""; // Assuming Flask serves from the root

// DOM Elements
const questionSetSelect = document.getElementById('question-set-select');
const questionSelect = document.getElementById('question-select');
const questionTextDisplay = document.getElementById('question-text-display');
const visualizationArea = document.getElementById('visualization-area');
const errorDisplay = document.getElementById('error-display');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM fully loaded and parsed.");
    // Add event listeners
    questionSetSelect.addEventListener('change', handleQuestionSetChange);
    questionSelect.addEventListener('change', handleQuestionSelectionChange);

    // Initial load
    fetchQuestionSets();
});

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
    console.log(`Solving and visualizing question index: ${questionIndex}`);
    if (questionIndex < 0 || questionIndex >= window.currentQuestions.length) {
        showError("Invalid question index.");
        return;
    }
    clearError();
    clearVisualization();
    const questionData = window.currentQuestions[questionIndex];
    questionTextDisplay.textContent = `Solving: ${questionData.question}`; // Show solving status

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

        // Step 2: Get visualization data
        console.log("Calling /api/visualization-data");
        const vizResponse = await fetch(`${API_BASE_URL}/api/visualization-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question_data: questionData, results: solveResult.results })
        });
        if (!vizResponse.ok) {
             const errorData = await vizResponse.json().catch(() => ({ error: `Viz request failed! status: ${vizResponse.status}` }));
            throw new Error(`Visualization Error: ${errorData.error || `HTTP status ${vizResponse.status}`}`);
        }
        const vizData = await vizResponse.json();
        console.log("Visualization data received:", vizData);

        // Step 3: Render the visualization
        renderVisualization(vizData);
        // Update question text display after successful processing
        questionTextDisplay.textContent = vizData.question_text || questionData.question;


    } catch (error) {
        console.error('Error during solve/visualize process:', error);
        showError(`Processing Error: ${error.message}`);
        // Reset question text if error occurs after starting
         questionTextDisplay.textContent = questionData.question;
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

function renderVisualization(vizData) {
    console.log("Rendering detailed visualization...");
    visualizationArea.innerHTML = ''; // Clear previous content

    if (!vizData || !vizData.bars || vizData.bars.length === 0) {
        visualizationArea.innerHTML = '<p>No visualization data available.</p>';
        return;
    }

    const maxValue = vizData.max_value > 0 ? vizData.max_value : 1; // Avoid division by zero, ensure positive

    // Determine a suitable width scaling factor if bars exceed container?
    // For now, assume bars fit, use percentages.

    // Render bars (data is already bottom-up if backend reversed it)
    vizData.bars.forEach(barData => {
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';

        // Create the main bar div (flex container for segments)
        const barElement = document.createElement('div');
        barElement.className = 'bar';

        let currentOffsetPercent = 0;
        // Add segments
        barData.segments.forEach(segment => {
            const segmentElement = document.createElement('div');
            segmentElement.className = 'bar-segment';

            // Calculate width based on segment's value relative to the *maximum value across all bars*
            // This ensures bars are scaled relative to each other.
            const segmentWidthPercent = (segment.value / maxValue) * 100;
            segmentElement.style.width = `${segmentWidthPercent}%`;
            segmentElement.style.backgroundColor = segment.color || '#cccccc';

            // Apply hatching based on pattern string or boolean
            if (segment.hatch) {
                if (segment.hatch_pattern === "///") {
                    segmentElement.classList.add('hatch-pattern-forward-slash');
                } else if (segment.hatch_pattern === "xxx") {
                    segmentElement.classList.add('hatch-pattern-cross');
                } else { // Default hatching if only true
                     segmentElement.classList.add('hatch-pattern-forward-slash');
                }
                 // Ensure background color is somewhat visible under hatching if not transparent
                 if (segment.color !== 'transparent') {
                    // You might need to adjust the hatch CSS to use RGBA or have a background set
                 } else {
                    segmentElement.style.backgroundColor = 'transparent'; // Ensure transparent background for hatch only
                 }
            }

            barElement.appendChild(segmentElement);
            currentOffsetPercent += segmentWidthPercent; // Track offset for annotations
        });

        // Add bar leader label (name and total value)
        const leaderLabelElement = document.createElement('span');
        leaderLabelElement.className = 'bar-leader-label';
        leaderLabelElement.textContent = `${barData.name}: ${barData.total_value.toFixed(1)}`;
        // Adjust leader line start based on bar width percentage
        const barWidthPercent = (barData.total_value / maxValue) * 100;
        // Position label relative to the end of the calculated bar width
        leaderLabelElement.style.left = `calc(${barWidthPercent}% + 5px)`; // Position just right of the bar end


        // Add annotations (dimension lines/labels)
        if (barData.annotations) {
            barData.annotations.forEach(anno => {
                const startPercent = (anno.start_value / maxValue) * 100;
                const endPercent = (anno.end_value / maxValue) * 100;
                const widthPercent = endPercent - startPercent;
                const midPercent = startPercent + widthPercent / 2;
                const levelClass = `level-${anno.level || 1}`; // Default to level 1

                // Horizontal Line
                const line = document.createElement('div');
                line.className = `annotation-line ${levelClass}`;
                line.style.left = `${startPercent}%`;
                line.style.width = `${widthPercent}%`;
                barContainer.appendChild(line);

                // Start Tick
                const tickStart = document.createElement('div');
                tickStart.className = `annotation-tick ${levelClass}`;
                tickStart.style.left = `${startPercent}%`;
                barContainer.appendChild(tickStart);

                // End Tick
                const tickEnd = document.createElement('div');
                tickEnd.className = `annotation-tick ${levelClass}`;
                tickEnd.style.left = `${endPercent}%`;
                barContainer.appendChild(tickEnd);

                // Label
                const label = document.createElement('div');
                label.className = `annotation-label ${levelClass}`;
                label.style.left = `${midPercent}%`;
                label.textContent = anno.label;
                barContainer.appendChild(label);
            });
        }


        // Add equation below the bar if available
        let equationElement = null;
        if (barData.equation) {
            equationElement = document.createElement('div');
            equationElement.className = 'equation-text';
            equationElement.textContent = barData.equation;
        }

        // Assemble the container
        barContainer.appendChild(barElement);
        barContainer.appendChild(leaderLabelElement);
        if (equationElement) {
            barContainer.appendChild(equationElement);
        }

        visualizationArea.appendChild(barContainer);
    });

    console.log("Detailed rendering complete.");
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
}