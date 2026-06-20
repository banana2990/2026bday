import os
import requests
from datetime import datetime
from flask import Flask, render_template, redirect, request, session, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ── 환경변수 ──────────────────────────────────────────────────────
KAKAO_JS_KEY       = os.environ.get("KAKAO_JAVASCRIPT_KEY", "")
KAKAO_REST_KEY     = os.environ.get("KAKAO_REST_API_KEY", "")
KAKAO_REDIRECT_URI = os.environ.get(
    "KAKAO_REDIRECT_URI",
    "https://kimsquiz2026.onrender.com/auth/kakao/callback"
)

# ── DB 모델 ───────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"
    # 내부 식별용 PK (Auto-increment)
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 로그인 타입 구분 ('kakao' 또는 'local')
    login_type    = db.Column(db.String(10), nullable=False, default='local')
    # 카카오 고유 식별 통합 번호 (일반 유저는 Null)
    kakao_id      = db.Column(db.BigInteger, unique=True, nullable=True)
    # 일반 로그인용 ID (카카오 유저는 Null 가능)
    username      = db.Column(db.String(50), unique=True, nullable=True)
    # 암호화된 비밀번호 해시값 (카카오 유저는 Null)
    password_hash = db.Column(db.String(255), nullable=True)

    nickname      = db.Column(db.String(100))
    profile_image = db.Column(db.String(500))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy=True)
    messages      = db.relationship("Message",      backref="user", lazy=True)

    # 비밀번호 해시화 암호화 (Spring Security의 PasswordEncoder 역할)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 비밀번호 검증 매칭
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_correct = db.Column(db.Boolean,  nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = "messages"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 모델 정의 후 테이블 자동 생성
with app.app_context():
    db.create_all()

# ── 라우트 ────────────────────────────────────────────────────────

@app.route("/")
def home():
    user = None
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
    return render_template(
        "index.html",
        kakao_js_key=KAKAO_JS_KEY,
        kakao_redirect_uri=KAKAO_REDIRECT_URI,
        user=user,
    )


# [OAuth] 카카오 로그인 콜백 처리
@app.route("/auth/kakao/callback")
def kakao_callback():
    code  = request.args.get("code")
    error = request.args.get("error")

    if error or not code:
        reason = request.args.get("error_description", "로그인이 취소되었습니다.")
        return redirect(url_for("home") + f"?login_error={reason}")

    # 1) 인가 코드 → 액세스 토큰
    token_res = requests.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type":   "authorization_code",
            "client_id":    KAKAO_REST_KEY,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code":         code,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    if token_res.status_code != 200:
        return redirect(url_for("home") + "?login_error=토큰 발급에 실패했습니다.")

    access_token = token_res.json().get("access_token")

    # 2) 액세스 토큰 → 사용자 정보
    user_res = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if user_res.status_code != 200:
        return redirect(url_for("home") + "?login_error=사용자 정보 조회에 실패했습니다.")

    data     = user_res.json()
    kakao_id = data["id"]
    profile  = data.get("kakao_account", {}).get("profile", {})
    nickname = profile.get("nickname", "")
    img_url  = profile.get("profile_image_url", "")

    # 3) DB upsert (kakao_id 기준 조회)
    user = User.query.filter_by(kakao_id=kakao_id).first()
    if user is None:
        user = User(
            kakao_id=kakao_id,
            login_type="kakao",
            nickname=nickname,
            profile_image=img_url
        )
        db.session.add(user)
    else:
        user.nickname      = nickname
        user.profile_image = img_url
        user.last_login_at = datetime.utcnow()
    db.session.commit()

    # 4) 세션 저장 (내부 고유 PK인 user.id 저장)
    session["user_id"]       = user.id
    session["nickname"]      = nickname
    session["profile_image"] = img_url

    return redirect(url_for("home"))


# [Local] 일반 회원가입 처리
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    nickname = request.form.get("nickname")

    if not username or not password or not nickname:
        return redirect(url_for("home") + "?login_error=모든 필드를 입력해주세요.")

    # 중복 아이디 체크
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return redirect(url_for("home") + "?login_error=이미 존재하는 아이디입니다.")

    # 새 유저 등록 및 패스워드 암호화
    new_user = User(username=username, nickname=nickname, login_type="local")
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # 가입 직후 세션 로그인 처리
    session["user_id"] = new_user.id
    session["nickname"] = new_user.nickname

    return redirect(url_for("home"))


# [Local] 일반 로그인 처리
@app.route("/login", methods=["POST"])
def local_login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.query.filter_by(username=username, login_type="local").first()

    # 유저 체크 및 비밀번호 해시값 대조
    if user and user.check_password(password):
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        session["user_id"] = user.id
        session["nickname"] = user.nickname
        session["profile_image"] = user.profile_image
        return redirect(url_for("home"))

    flash("아이디 또는 비밀번호가 틀렸습니다.", "login_error")
    return redirect(url_for("home"))

# [Local] 비밀번호 초기화(재설정) 처리
@app.route("/reset-password", methods=["POST"])
def reset_password():
    username     = request.form.get("username")
    nickname     = request.form.get("nickname")
    new_password = request.form.get("new_password")

    if not username or not nickname or not new_password:
        flash("모든 필드를 입력해주세요.", "login_error") # 덮어씌울 파라미터 이름 역할을 '카테고리'로 줍니다.
        return redirect(url_for("home"))

    user = User.query.filter_by(username=username, nickname=nickname, login_type="local").first()

    if user:
        user.set_password(new_password)
        db.session.commit()
        flash("비밀번호가 성공적으로 변경되었습니다. 로그인 해주세요.", "login_success") # 세션 플래시 저장
        return redirect(url_for("home")) # URL 뒤에 아무것도 안 붙고 깔끔하게 이동!

    flash("일치하는 회원 정보가 없습니다.", "login_error")
    return redirect(url_for("home"))

# [Local] 회원가입 아이디 중복 확인 API (JSON 반환)
@app.route("/check-username", methods=["POST"])
def check_username():
    # AJAX 요청으로 보낸 JSON 데이터를 파싱합니다.
    data = request.get_json()
    if not data or "username" not in data:
        return jsonify({"is_available": False, "message": "아이디를 입력해주세요."}), 400

    username = data["username"].strip()
    if not username:
        return jsonify({"is_available": False, "message": "공백은 아이디로 사용할 수 없습니다."}), 400

    # DB에서 해당 아이디가 존재하는지 쿼리
    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({"is_available": False, "message": "이미 사용 중인 아이디입니다."})

    return jsonify({"is_available": True, "message": "사용 가능한 아이디입니다."})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)