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

            // 정답 강조
            if (optIdx === correctIdx) {
                className += ' olive-bg';
            }
            // 오답 체크 (내가 고른 게 틀렸을 때만 빨간색)
            else if (optIdx === userSelected && userSelected !== correctIdx) {
                className += ' red-bg';
            }

            optionsHtml += `<div class="${className}">${optIdx + 1}. ${opt}</div>`;
        });

        item.innerHTML = `<p><strong>${q.id}. ${q.question}</strong></p>${optionsHtml}`;
        container.appendChild(item);
    });
});