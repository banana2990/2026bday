let userAnswers = new Array(quizData.length).fill(null);
let currentIdx = 0;

const questionText = document.getElementById('question-text');
const optionsContainer = document.getElementById('options-container');
const dotsContainer = document.getElementById('dots-container');
const progressText = document.getElementById('quiz-progress-text');
const submitBtn = document.getElementById('submit-quiz-btn');
const hiddenInput = document.getElementById('answers-hidden-input');

function initDots() {
    dotsContainer.innerHTML = "";
    for(let i = 0; i < quizData.length; i++) {
        const dot = document.createElement('div');
        dot.className = 'dot';
        dot.addEventListener('click', () => goToQuestion(i));
        dotsContainer.appendChild(dot);
    }
}

function renderQuiz() {
    const currentQuiz = quizData[currentIdx];
    progressText.innerText = `📋 문제 ${currentQuiz.id} / ${quizData.length}`;
    questionText.innerText = currentQuiz.question;
    optionsContainer.innerHTML = "";
    currentQuiz.options.forEach((option, optIdx) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.type = 'button';
        btn.innerText = `${optIdx + 1}. ${option}`;
        if(userAnswers[currentIdx] === optIdx) btn.classList.add('selected');
        btn.addEventListener('click', () => selectOption(optIdx));
        optionsContainer.appendChild(btn);
    });
    updateDotsUI();
    checkSubmitCondition();
}

function selectOption(optIdx) {
    document.body.style.pointerEvents = 'none';
    userAnswers[currentIdx] = optIdx;
    renderQuiz();
    setTimeout(() => {
        document.body.style.pointerEvents = 'auto';
        if (currentIdx < quizData.length - 1) {
            currentIdx++;
            renderQuiz();
        }
    }, 1000);
}

function updateDotsUI() {
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, i) => {
        dot.classList.remove('active', 'marked');
        if (i === currentIdx) dot.classList.add('active');
        if (userAnswers[i] !== null) dot.classList.add('marked');
    });
}

function goToQuestion(idx) {
    currentIdx = idx;
    renderQuiz();
}

function checkSubmitCondition() {
    const isAllAnswered = userAnswers.every(ans => ans !== null);
    const isLastPage = (currentIdx === quizData.length - 1);
    if (isAllAnswered && isLastPage) {
        hiddenInput.value = JSON.stringify(userAnswers);
        submitBtn.style.display = 'block';
    } else {
        submitBtn.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initDots();
    renderQuiz();
});