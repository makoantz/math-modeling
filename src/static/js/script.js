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
    console.log("Rendering detailed visualization with SVG (v2)...");
    visualizationArea.innerHTML = ''; // Clear previous content

    if (!vizData || !vizData.bars || vizData.bars.length === 0) {
        visualizationArea.innerHTML = '<p>No visualization data available.</p>';
        return;
    }

    const maxValue = vizData.max_value > 0 ? vizData.max_value : 1;
    const svgAnnotationHeight = 55; // Total height for SVG area
    const barHeight = 25;
    const barMarginTop = svgAnnotationHeight + 5; // Bar's top edge relative to container top
    const equationBottomMargin = 5; // Space from bottom for equation
    const equationHeightEstimate = 15; // Estimated height for equation text
    // Calculate total height needed for the container
    const totalBarContainerHeight = barMarginTop + barHeight + equationBottomMargin + equationHeightEstimate;

    const svgNS = "http://www.w3.org/2000/svg";

    vizData.bars.forEach(barData => {
        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        barContainer.style.minHeight = `${totalBarContainerHeight}px`; // Ensure container has enough height


        // --- Create SVG for Annotations ---
        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute('class', 'annotation-svg');
        svg.setAttribute('height', svgAnnotationHeight); // Set fixed height
        svg.setAttribute('viewBox', `0 0 ${maxValue} ${svgAnnotationHeight}`);
        svg.setAttribute('preserveAspectRatio', 'none');

        // --- Draw Annotations in SVG ---
        if (barData.annotations) {
            barData.annotations.forEach(anno => {
                const startX = anno.start_value;
                const endX = anno.end_value;
                const midX = startX + (endX - startX) / 2;
                const level = anno.level || 1;

                // Y positions within SVG (0=top)
                const lineY = (level === 1) ? 35 : 15; // Level 1 lower, Level 2 higher
                const textY = lineY - 2; // Position text baseline slightly ABOVE the line
                const tickStartY = lineY;
                const tickEndY = lineY + 4; // Tick length (downwards)

                // Horizontal Line
                const hLine = document.createElementNS(svgNS, "line");
                hLine.setAttribute('x1', startX);
                hLine.setAttribute('y1', lineY);
                hLine.setAttribute('x2', endX);
                hLine.setAttribute('y2', lineY);
                // No specific class needed if styling all lines the same
                svg.appendChild(hLine);

                // Start Tick
                const tickStart = document.createElementNS(svgNS, "line");
                tickStart.setAttribute('x1', startX);
                tickStart.setAttribute('y1', tickStartY);
                tickStart.setAttribute('x2', startX);
                tickStart.setAttribute('y2', tickEndY);
                svg.appendChild(tickStart);

                // End Tick
                const tickEnd = document.createElementNS(svgNS, "line");
                tickEnd.setAttribute('x1', endX);
                tickEnd.setAttribute('y1', tickStartY);
                tickEnd.setAttribute('x2', endX);
                tickEnd.setAttribute('y2', tickEndY);
                svg.appendChild(tickEnd);

                // Label Text
                const label = document.createElementNS(svgNS, "text");
                label.setAttribute('x', midX);
                label.setAttribute('y', textY); // Use adjusted Y
                // No specific class needed if styling all text the same
                label.textContent = anno.label;
                svg.appendChild(label);
            });
        }

        // --- Create the Bar Element ---
        const barElement = document.createElement('div');
        barElement.className = 'bar';
        barElement.style.height = `${barHeight}px`;
        barElement.style.top = `${barMarginTop}px`; // Position below SVG using 'top'

        // Add segments (Logic remains similar)
        barData.segments.forEach(segment => {
            const segmentElement = document.createElement('div');
            segmentElement.className = 'bar-segment';
            const segmentWidthPercent = (segment.value / maxValue) * 100;
            segmentElement.style.width = `max(0%, ${segmentWidthPercent}%)`;
            segmentElement.style.backgroundColor = segment.color || '#cccccc';
            if (segment.hatch) {
                const hatchClass = segment.hatch_pattern === "xxx" ? 'hatch-pattern-cross' : 'hatch-pattern-forward-slash';
                segmentElement.classList.add(hatchClass);
                if (segment.color === 'transparent') {
                    segmentElement.style.backgroundColor = 'transparent';
                }
            }
            barElement.appendChild(segmentElement);
        });


        // --- Create Leader Label ---
        const leaderLabelElement = document.createElement('span');
        leaderLabelElement.className = 'bar-leader-label';
        leaderLabelElement.textContent = `${barData.name}: ${barData.total_value.toFixed(1)}`;
        leaderLabelElement.style.top = `${barMarginTop}px`; // Align top with bar's top
        leaderLabelElement.style.transform = `translateY(${barHeight / 2}px)`; // Center vertically on bar
        const barWidthPercent = (barData.total_value / maxValue) * 100;
        // Ensure label doesn't overlap bar if bar is very wide
        leaderLabelElement.style.left = `calc(min(100%, ${barWidthPercent}%) + 5px)`;


        // --- Create Equation Text ---
        let equationElement = null;
        if (barData.equation) {
            equationElement = document.createElement('div');
            equationElement.className = 'equation-text';
            // CSS handles positioning (absolute bottom)
            equationElement.textContent = barData.equation;
        }


        // --- Assemble the container ---
        barContainer.appendChild(svg);
        barContainer.appendChild(barElement);
        barContainer.appendChild(leaderLabelElement);
        if (equationElement) {
            barContainer.appendChild(equationElement);
        }

        visualizationArea.appendChild(barContainer);
    });

    console.log("SVG rendering update complete.");
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