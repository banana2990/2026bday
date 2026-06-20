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


// 중복 확인 여부를 체크하는 상태 변수
let isUsernameChecked = false;

/**
 * 아이디 중복 확인 함수 (비동기 Fetch API)
 */
function checkDuplicateUsername() {
    const usernameInput = document.getElementById('reg-username');
    const msgDiv = document.getElementById('username-check-msg');
    const submitBtn = document.getElementById('reg-submit-btn');

    const username = usernameInput.value.trim();

    if (!username) {
        alert("아이디를 입력해주세요.");
        return;
    }

    // Flask 백엔드로 비동기 POST 요청 전송
    fetch('/check-username', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: username })
    })
        .then(response => response.json())
        .then(data => {
            msgDiv.style.display = 'block';
            msgDiv.innerText = data.message;

            if (data.is_available) {
                // 사용 가능할 때: 메시지 초록색, 회원가입 버튼 활성화
                msgDiv.style.color = '#2e7d32';
                submitBtn.disabled = false;
                submitBtn.style.backgroundColor = '#4a90e2';
                submitBtn.style.cursor = 'pointer';
                isUsernameChecked = true;
            } else {
                // 사용 불가능할 때: 메시지 빨간색, 회원가입 버튼 비활성화维持
                msgDiv.style.color = '#c62828';
                submitBtn.disabled = true;
                submitBtn.style.backgroundColor = '#cccccc';
                submitBtn.style.cursor = 'not-allowed';
                isUsernameChecked = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('중복 확인 중 오류가 발생했습니다.');
        });
}

// 사용자가 중복확인을 통과한 후 아이디를 다시 수정하면, 가입 버튼을 다시 잠그는 디테일 처리
window.addEventListener('DOMContentLoaded', () => {
    const usernameInput = document.getElementById('reg-username');
    if (usernameInput) {
        usernameInput.addEventListener('input', () => {
            if (isUsernameChecked) {
                isUsernameChecked = false;
                const msgDiv = document.getElementById('username-check-msg');
                const submitBtn = document.getElementById('reg-submit-btn');

                msgDiv.style.display = 'block';
                msgDiv.style.color = '#e65100';
                msgDiv.innerText = "아이디가 변경되었습니다. 다시 중복확인을 해주세요.";

                submitBtn.disabled = true;
                submitBtn.style.backgroundColor = '#cccccc';
                submitBtn.style.cursor = 'not-allowed';
            }
        });
    }
});

/**
 *  화면 렌더링 섹션 전환 (SPA 방식)
 *  @param {string} targetId - 보여줄 영역의 ID ('auth-start', 'auth-login', 'auth-register')
 *  기존 showSection 보완: 화면을 전환할 때 중복확인 상태도 깨끗하게 리셋해줍니다.
 */
function showSection(targetId) {
    const sections = document.querySelectorAll('.auth-section');
    sections.forEach(section => { section.classList.remove('active'); });

    const targetSection = document.getElementById(targetId);
    if (targetSection) { targetSection.classList.add('active'); }

    // 배너 숨기기
    const errorBanner = document.querySelector('.error-banner');
    if (errorBanner) { errorBanner.style.display = 'none'; }
    const successBanner = document.querySelector('.success-banner');
    if (successBanner) { successBanner.style.display = 'none'; }

    // 회원가입창 리셋 로직
    if (targetId !== 'auth-register') {
        isUsernameChecked = false;
        const msgDiv = document.getElementById('username-check-msg');
        if (msgDiv) msgDiv.style.display = 'none';
        const submitBtn = document.getElementById('reg-submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.style.backgroundColor = '#cccccc';
            submitBtn.style.cursor = 'not-allowed';
        }
        const regForm = document.getElementById('register-form');
        if (regForm) regForm.reset();
    }
}