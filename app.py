import os
import requests
from datetime import datetime

from flask import Flask, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

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
    id            = db.Column(db.BigInteger, primary_key=True)   # 카카오 회원번호
    nickname      = db.Column(db.String(100))
    profile_image = db.Column(db.String(500))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy=True)
    messages      = db.relationship("Message",      backref="user", lazy=True)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    is_correct = db.Column(db.Boolean,  nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = "messages"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

    # 3) DB upsert
    user = db.session.get(User, kakao_id)
    if user is None:
        user = User(id=kakao_id, nickname=nickname, profile_image=img_url)
        db.session.add(user)
    else:
        user.nickname      = nickname
        user.profile_image = img_url
        user.last_login_at = datetime.utcnow()
    db.session.commit()

    # 4) 세션 저장
    session["user_id"]       = kakao_id
    session["nickname"]      = nickname
    session["profile_image"] = img_url

    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ── DB 초기화 CLI ─────────────────────────────────────────────────

@app.cli.command("init-db")
def init_db():
    with app.app_context():
        db.create_all()
    print("DB 테이블이 생성되었습니다.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)