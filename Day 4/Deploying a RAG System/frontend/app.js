const API_BASE = 'http://localhost:8000/api';

// State
let quizData = [];
let currentQuestionIndex = 0;
let score = 0;
let timerInterval = null;
let timeLeft = 60; // 60 seconds per question or total? Let's do 60s per quiz for MVP.
let userAnswers = [];

// DOM Elements
const sections = {
    setup: document.getElementById('setup-section'),
    quiz: document.getElementById('quiz-section'),
    results: document.getElementById('results-section')
};

const loading = document.getElementById('loading');
const btnIngest = document.getElementById('btn-ingest');
const btnGenerate = document.getElementById('btn-generate');
const btnNext = document.getElementById('btn-next');
const btnRestart = document.getElementById('btn-restart');

// Initialization
btnIngest.addEventListener('click', async () => {
    const text = document.getElementById('knowledge-text').value;
    if (!text.trim()) return alert("Please enter some text to ingest.");
    
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/vectorize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        if(res.ok) {
            document.getElementById('ingest-status').textContent = `✅ Successfully ingested text into vectors.`;
        } else {
            alert(data.detail || "Error ingesting.");
        }
    } catch (err) {
        alert("Server error. Is the backend running?");
    } finally {
        showLoading(false);
    }
});

btnGenerate.addEventListener('click', async () => {
    const topic = document.getElementById('quiz-topic').value || 'General Knowledge';
    const count = parseInt(document.getElementById('quiz-count').value) || 3;
    
    showLoading(true);
    try {
        const res = await fetch(`${API_BASE}/quiz/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, count })
        });
        const data = await res.json();
        
        if (res.ok) {
            quizData = data.questions;
            startQuiz();
        } else {
            alert(data.detail || "Failed to generate quiz.");
        }
    } catch (err) {
        alert("Server error. Is the backend running?");
    } finally {
        showLoading(false);
    }
});

function startQuiz() {
    currentQuestionIndex = 0;
    score = 0;
    userAnswers = [];
    timeLeft = quizData.length * 20; // 20 seconds per question as total timer
    
    switchSection('quiz');
    renderQuestion();
    startTimer();
}

function renderQuestion() {
    const container = document.getElementById('question-container');
    const question = quizData[currentQuestionIndex];
    btnNext.disabled = true;
    btnNext.textContent = currentQuestionIndex === quizData.length - 1 ? "Finish Quiz" : "Next Question";

    let html = `<h3>Q${currentQuestionIndex + 1}: ${question.question}</h3><div class="options-container mt-4">`;
    
    question.options.forEach((opt, idx) => {
        html += `<button class="option-btn" data-index="${idx}">${opt}</button>`;
    });
    html += `</div><div id="explanation-container" style="display:none;" class="explanation-box"></div>`;
    
    container.innerHTML = html;

    // Attach logic to options
    const optionBtns = container.querySelectorAll('.option-btn');
    optionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => handleOptionSelect(e, parseInt(btn.dataset.index), optionBtns, question));
    });
}

function handleOptionSelect(e, selectedIndex, allBtns, question) {
    if(!btnNext.disabled) return; // Prevent changing answer
    
    const correctIndex = question.answer_index;
    const isCorrect = selectedIndex === correctIndex;
    
    if (isCorrect) score++;
    
    userAnswers.push({
        question: question.question,
        selected: question.options[selectedIndex],
        correct: question.options[correctIndex],
        isCorrect,
        explanation: question.explanation
    });

    // Styling
    allBtns.forEach((btn, idx) => {
        btn.disabled = true;
        if (idx === correctIndex) btn.classList.add('correct');
        else if (idx === selectedIndex) btn.classList.add('wrong');
    });

    // Show explanation
    const expContainer = document.getElementById('explanation-container');
    expContainer.style.display = 'block';
    expContainer.innerHTML = `<strong>Explanation:</strong> ${question.explanation}`;

    btnNext.disabled = false;
}

btnNext.addEventListener('click', () => {
    currentQuestionIndex++;
    if (currentQuestionIndex >= quizData.length) {
        endQuiz();
    } else {
        renderQuestion();
    }
});

btnRestart.addEventListener('click', () => {
    switchSection('setup');
});

function startTimer() {
    document.getElementById('time-left').textContent = formatTime(timeLeft);
    clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        timeLeft--;
        document.getElementById('time-left').textContent = formatTime(timeLeft);
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            endQuiz();
        }
    }, 1000);
}

function endQuiz() {
    clearInterval(timerInterval);
    switchSection('results');
    document.getElementById('final-score').textContent = score;
    document.getElementById('total-score').textContent = quizData.length;
    
    // Render details
    let detailsHtml = '';
    userAnswers.forEach((ans, i) => {
        detailsHtml += `
            <div class="result-item">
                <h4>${i + 1}. ${ans.question}</h4>
                <p>Your answer: <span style="color: ${ans.isCorrect ? 'var(--success)' : 'var(--danger)'};">${ans.selected}</span></p>
                ${!ans.isCorrect ? `<p>Correct answer: <strong>${ans.correct}</strong></p>` : ''}
            </div>
        `;
    });
    document.getElementById('results-details').innerHTML = detailsHtml;
}

function switchSection(secId) {
    Object.values(sections).forEach(s => s.classList.remove('active'));
    sections[secId].classList.add('active');
}

function formatTime(seconds) {
    if(seconds < 0) seconds = 0;
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

function showLoading(show) {
    if(show) loading.classList.remove('hidden');
    else loading.classList.add('hidden');
}
