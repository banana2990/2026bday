/**
 * 🎁 퀴즈 점수별 상품 분기 매니저
 */
const PrizeManager = {
    // 1) 원천 데이터 마스터 테이블 (한 곳에서만 수정하면 전체 반영)
    prizes: [
        { condition: (score) => score === 100, name: "👑 1등 명예의 전당 상품 (기프티콘 3만원권)" },
        { condition: (score) => score >= 80,  name: "🎁 2등 김예진 박사상 상품 (스타벅스 디저트 세트)" },
        { condition: (score) => score >= 50,  name: "☕ 3등 아차상 상품 (바나나우유 기프티콘)" },
        { condition: (score) => true,         name: "🤍 참가상 (김예진의 진심 어린 사랑과 감사)" } // Default
    ],

    /**
     * 점수를 기반으로 한글 상품명을 반환합니다.
     * @param {number} score
     * @returns {string} prizeName
     */
    getPrizeName: function(score) {
        const parsedScore = parseInt(score, 10) || 0;
        // 조건이 만족하는 첫 번째 타겟 아이템을 찾아 명칭을 리턴
        const target = this.prizes.find(p => p.condition(parsedScore));
        return target ? target.name : "🤍 참가상";
    }
};

// 타 페이지 script 전역 연동을 위해 window에 탑재
window.PrizeManager = PrizeManager;