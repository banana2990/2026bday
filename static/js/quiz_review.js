document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById('review-list');

    // 데이터 확인용 (개발자 도구 콘솔에서 확인 가능)
    console.log("사용자 답안:", userAnswers);
    console.log("정답지:", correct_sheet);

    quizData.forEach((q, i) => {
        // userAnswers가 배열인지 확인하고 인덱스 접근
        const userSelected = (userAnswers && userAnswers[i] !== undefined) ? userAnswers[i] : -1;
        const correctIdx = correct_sheet[i];

        const item = document.createElement('div');
        item.className = 'question-item';

        let optionsHtml = '';
        q.options.forEach((opt, optIdx) => {
            let className = 'option-box';

            // 1. [정답] 무조건 올리브색
            if (optIdx === correctIdx) {
                className += ' olive-bg';
            }
            // 2. [오답] 사용자가 선택한 답인데, 정답이 아닌 경우 빨간색
            else if (optIdx === userSelected) {
                className += ' red-bg';
            }

            optionsHtml += `<div class="${className}">${optIdx + 1}. ${opt}</div>`;
        });

        item.innerHTML = `<p><strong>${q.id}. ${q.question}</strong></p>${optionsHtml}`;
        container.appendChild(item);
    });
});