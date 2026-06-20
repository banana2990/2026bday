// 카카오 로그인 관련 상태 관리 전역 변수
let kakaoRedirectUri = "";

/**
 * 카카오 SDK 초기화 및 환경변수 설정
 */
function initKakao(jsKey, redirectUri) {
    kakaoRedirectUri = redirectUri;
    if (typeof Kakao !== 'undefined' && !Kakao.isInitialized()) {
        Kakao.init(jsKey);
    }
}

/**
 * 카카오 인가 코드 요청 실행
 */
function kakaoLogin() {
    if (typeof Kakao !== 'undefined') {
        Kakao.Auth.authorize({
            redirectUri: kakaoRedirectUri,
        });
    } else {
        alert("카카오 SDK 로드에 실패했습니다.");
    }
}

/**
 * 화면 렌더링 섹션 전환 (SPA 방식)
 * @param {string} targetId - 보여줄 영역의 ID ('auth-start', 'auth-login', 'auth-register')
 */
function showSection(targetId) {
    // 1. 모든 인증 섹션을 숨깁니다.
    const sections = document.querySelectorAll('.auth-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    // 2. 타겟이 되는 섹션만 노출시킵니다.
    const targetSection = document.getElementById(targetId);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // 3. 화면 전환 시 기존에 떠있던 에러 배너가 있다면 가독성을 위해 숨겨줍니다.
    const errorBanner = document.querySelector('.error-banner');
    if (errorBanner) {
        errorBanner.style.display = 'none';
    }
}

// 만약 백엔드에서 에러 피드백을 갖고 세로고침 되었다면, 로그인/회원가입 화면을 유지해주는 디테일 예외 처리
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('login_error')) {
        // 회원가입 실패 실패라면 회원가입창 유지, 그 외엔 로그인창 유지
        const errorMsg = urlParams.get('login_error');
        if (errorMsg.includes('아이디입니다') || errorMsg.includes('필드를 입력')) {
            showSection('auth-register');
        } else {
            showSection('auth-login');
        }
    }
});