/**
 * 🎁 퀴즈 점수별 상품 분기 매니저
 */
const PrizeManager = {
    // 1) 원천 데이터 마스터 테이블 (한 곳에서만 수정하면 전체 반영)
    prizes: [
        { condition: (score) => score === 100, name: "👑 명예의 전당 : 김예진과 식사권 / 편의점 상품권 2만원권" },
        { condition: (score) => score >= 95,   name: "🎁 예진학 박사 : 김예진과 커피권 / 편의점 상품권 1만원권" },
        { condition: (score) => score >= 70,   name: "🎁 예진학 석사 : 폴바셋 룽고 1잔" },
        { condition: (score) => score >= 40,   name: "🎁 예진학 학사 : 메로나 1개" },
        { condition: (score) => score >= 5,    name: "🤍 특별 참가상 : 비타500 1병" },
        { condition: (score) => true,          name: "어쩜 이러실 수 있어요 : 김예진과 강제 커피권" } // Default
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