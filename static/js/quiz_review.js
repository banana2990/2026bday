document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById('review-list');

    quizData.forEach((q, i) => {
        const userSelected = userAnswers[i];
        const correctIdx = correct_sheet[i];
        const item = document.createElement('div');
        item.className = 'question-item';

        let optionsHtml = '';
        q.options.forEach((opt, optIdx) => {
            let className = 'option-box';

            // 1. [정답]은 무조건 올리브색 + 굵게
            if (optIdx === correctIdx) {
                className += ' olive-bg';
            }
            // 2. [오답] 내가 선택한 것인데 정답이 아닌 경우만 빨간색
            else if (optIdx === userSelected) {
                className += ' red-bg';
            }

            optionsHtml += `<div class="${className}">${optIdx + 1}. ${opt}</div>`;
        });

        item.innerHTML = `<p><strong>${q.id}. ${q.question}</strong></p>${optionsHtml}`;
        container.appendChild(item);
    });
});