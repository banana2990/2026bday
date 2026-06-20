import json
import os
import requests
from datetime import datetime
from flask import Flask, render_template, redirect, request, session, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
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
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login_type    = db.Column(db.String(10), nullable=False, default='local')
    kakao_id      = db.Column(db.BigInteger, unique=True, nullable=True)
    username      = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)

    nickname      = db.Column(db.String(100))
    profile_image = db.Column(db.String(500))
    contact_info  = db.Column(db.String(255), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 관리자 발송 처리를 위한 컬럼
    sent_at       = db.Column(db.DateTime, nullable=True)

    # 연관 관계 정의 (backref를 통해 상대 모델에서 .user 로 접근 가능)
    quiz_attempts = db.relationship("QuizAttempt", backref="user", lazy=True)
    memos         = db.relationship("UserMemo", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    correct_count = db.Column(db.Integer, nullable=False, default=0)
    total_score   = db.Column(db.Integer, nullable=False, default=0)
    selected_answers = db.Column(db.Text, nullable=False)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


class UserMemo(db.Model):
    __tablename__ = 'user_memos'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    bg_color   = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
        flash(reason, "login_error")
        return redirect(url_for("home"))

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
        flash("토큰 발급에 실패했습니다.", "login_error")
        return redirect(url_for("home"))

    access_token = token_res.json().get("access_token")

    # 2) 액세스 토큰 → 사용자 정보
    user_res = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if user_res.status_code != 200:
        flash("사용자 정보 조회에 실패했습니다.", "login_error")
        return redirect(url_for("home"))

    data     = user_res.json()
    kakao_id = data["id"]
    profile  = data.get("kakao_account", {}).get("profile", {})
    nickname = profile.get("nickname", "")
    img_url  = profile.get("profile_image_url", "")

    # 3) DB upsert
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

    # 4) 세션 저장
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
        flash("모든 필드를 입력해주세요.", "login_error")
        return redirect(url_for("home"))

    # 중복 아이디 체크
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("이미 존재하는 아이디입니다.", "login_error")
        return redirect(url_for("home"))

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
        flash("모든 필드를 입력해주세요.", "login_error")
        return redirect(url_for("home"))

    user = User.query.filter_by(username=username, nickname=nickname, login_type="local").first()

    if user:
        user.set_password(new_password)
        db.session.commit()
        flash("비밀번호가 성공적으로 변경되었습니다. 로그인 해주세요.", "login_success")
        return redirect(url_for("home"))

    flash("일치하는 회원 정보가 없습니다.", "login_error")
    return redirect(url_for("home"))


# [Local] 회원가입 아이디 중복 확인 API (JSON 반환)
@app.route("/check-username", methods=["POST"])
def check_username():
    data = request.get_json()
    if not data or "username" not in data:
        return jsonify({"is_available": False, "message": "아이디를 입력해주세요."}), 400

    username = data["username"].strip()
    if not username:
        return jsonify({"is_available": False, "message": "공백은 아이디로 사용할 수 없습니다."}), 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({"is_available": False, "message": "이미 사용 중인 아이디입니다."})

    return jsonify({"is_available": True, "message": "사용 가능한 아이디입니다."})


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# [Quiz] 퀴즈 시작 전 진입 게이트웨이 라우트
@app.route("/quiz/start")
def quiz_start_page():
    if "user_id" not in session:
        flash("로그인이 필요한 서비스입니다.", "login_error")
        return redirect(url_for("home"))

    attempts_count = QuizAttempt.query.filter_by(user_id=session["user_id"]).count()

    if attempts_count >= 3:
        flash("이미 참여 기회를 모두 사용하셨습니다. <br/> (최대 3회)", "login_error")
        return redirect(url_for("home"))

    return render_template("quiz.html")


# [Quiz] 20문제 일괄 제출 및 채점 처리
@app.route("/submit-quiz", methods=["POST"])
def submit_quiz():
    if "user_id" not in session:
        flash("로그인이 필요한 서비스입니다.", "login_error")
        return redirect(url_for("home"))

    current_user_id = session["user_id"]
    existing_attempts_count = QuizAttempt.query.filter_by(user_id=current_user_id).count()

    if existing_attempts_count >= 3:
        flash("퀴즈 참여는 인당 최대 3회까지만 가능합니다.", "login_error")
        return redirect(url_for("home"))

    raw_answers = request.form.get("answers")
    if not raw_answers:
        flash("제출된 답안이 올바르지 않습니다.", "login_error")
        return redirect(url_for("home"))

    user_answers = json.loads(raw_answers)
    correct_sheet = [2, 1, 0, 1, 0, 1, 2, 2, 0, 2, 1, 0, 1, 1, 2, 0, 0, 1, 2, 0]

    correct_count = 0
    for idx, ans in enumerate(user_answers):
        if ans == correct_sheet[idx]:
            correct_count += 1

    total_score = correct_count * 5

    attempt = QuizAttempt(
        user_id=current_user_id,
        correct_count=correct_count,
        total_score=total_score,
        selected_answers=raw_answers
    )

    db.session.add(attempt)
    db.session.commit()

    session["last_correct_count"] = correct_count
    session["last_total_score"] = total_score

    return redirect(url_for("quiz_result"))


# [Quiz] 점수 정보 전달 및 결과 뷰 렌더링
@app.route("/quiz-result")
def quiz_result():
    if "user_id" not in session:
        return redirect(url_for("home"))

    score = session.get("last_total_score", 0)
    count = session.get("last_correct_count", 0)
    attempt_count = QuizAttempt.query.filter_by(user_id=session["user_id"]).count()

    # 🛠️ 비즈니스 로직(prize_name) 분기 구역을 완전히 제거하고 순수 데이터만 클라이언트로 전달합니다.
    return render_template(
        "result.html",
        score=score,
        count=count,
        attempt_count=attempt_count
    )


# [Quiz] 입력받은 연락처 최종 저장 후 홈으로 리다이렉트
@app.route("/submit-contact", methods=["POST"])
def submit_contact():
    if "user_id" not in session:
        return redirect(url_for("home"))

    contact_info = request.form.get("contact_info")

    if contact_info:
        user = db.session.get(User, session["user_id"])
        if user:
            user.contact_info = contact_info
            db.session.commit()
            flash("이벤트 응모가 완료되었습니다! 홈 화면으로 이동합니다.", "login_success")

    return redirect(url_for("home"))


# [Admin] 관리자 전용 페이지 뷰
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))

    current_user = db.session.get(User, session["user_id"])
    if not current_user or current_user.kakao_id != 4953979045:
        flash("관리자만 접근할 수 있습니다.", "login_error")
        return redirect(url_for("home"))

    valid_users = User.query.filter(User.contact_info.isnot(None)).all()
    contestants = []

    for u in valid_users:
        attempt_count = QuizAttempt.query.filter_by(user_id=u.id).count()
        if attempt_count == 0:
            continue

        max_score_query = db.session.query(func.max(QuizAttempt.total_score)).filter(QuizAttempt.user_id == u.id).scalar()
        display_score = max_score_query if max_score_query is not None else 0

        contestants.append({
            "id": u.id,
            "nickname": u.nickname,
            "contact_info": u.contact_info,
            "sent_at": u.sent_at,
            "attempt_count": attempt_count,
            "best_score": display_score
        })

    contestants = sorted(contestants, key=lambda x: x['best_score'], reverse=True)
    return render_template("admin.html", contestants=contestants)


# [Admin] 발송 완료 처리 비동기 API
@app.route("/admin/send-product/<int:target_user_id>", methods=["POST"])
def send_product(target_user_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "인증 정보가 없습니다."}), 401

    current_user = db.session.get(User, session["user_id"])

    if not current_user or current_user.kakao_id != 4953979045:
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    target_user = db.session.get(User, target_user_id)
    if not target_user:
        return jsonify({"success": False, "message": "존재하지 않는 사용자입니다."}), 442

    if target_user.sent_at:
        return jsonify({"success": False, "message": "이미 발송 처리가 완료된 사용자입니다."})

    target_user.sent_at = datetime.utcnow()
    db.session.commit()

    formatted_time = target_user.sent_at.strftime('%Y-%m-%d %H:%M:%S')

    return jsonify({
        "success": True,
        "message": "발송 처리가 완료되었습니다.",
        "sent_at": formatted_time
    })


# [Memo] 사용자가 메모 작성 페이지에 들어올 때 (앞문 단속)
@app.route("/memo")
def memo_page():
    if "user_id" not in session:
        flash("로그인이 필요한 서비스입니다.", "login_error")
        return redirect(url_for("home"))

    memo_count = UserMemo.query.filter_by(user_id=session["user_id"]).count()
    if memo_count >= 5:
        flash("이미 최대 메모 개수(5개)를 채우셨습니다. <br/> '내 기록 확인'에서 기존 메모를 관리해 주세요!", "login_error")
        return redirect(url_for("home"))

    colors = ['postit-yellow', 'postit-pink', 'postit-green', 'postit-blue']
    import random
    selected_color = random.choice(colors)

    return render_template("memo.html", selected_color=selected_color)


# [Memo] 사용자가 전송 버튼을 눌러 DB에 저장할 때 (뒷문 단속)
@app.route("/submit-memo", methods=["POST"])
def submit_memo():
    if "user_id" not in session:
        flash("로그인이 필요한 서비스입니다.", "login_error")
        return redirect(url_for("home"))

    current_user_id = session["user_id"]

    final_count = UserMemo.query.filter_by(user_id=current_user_id).count()
    if final_count >= 5:
        flash("메모는 인당 최대 5개까지만 남길 수 있습니다.", "login_error")
        return redirect(url_for("home"))

    content = request.form.get("content", "").strip()
    bg_color = request.form.get("bg_color", "postit-yellow")

    if not content:
        flash("메모 내용을 입력해 주세요.", "login_error")
        return redirect(url_for("memo_page"))

    new_memo = UserMemo(user_id=current_user_id, content=content, bg_color=bg_color)
    db.session.add(new_memo)
    db.session.commit()

    return redirect(url_for("home"))


# [Memo] 내 기록 및 메모 조회 뷰
@app.route("/my-records")
def my_records():
    if "user_id" not in session:
        flash("로그인이 필요한 서비스입니다.", "login_error")
        return redirect(url_for("home"))

    current_user_id = session["user_id"]
    current_user = db.session.get(User, current_user_id)

    attempts = QuizAttempt.query.filter_by(user_id=current_user_id).order_by(QuizAttempt.id.asc()).all()

    # 🛠️ prize 할당 로직을 제거하고, 순수 점수 데이터셋만 보냅니다.
    quiz_results = []
    for idx, att in enumerate(attempts):
        quiz_results.append({
            "round": idx + 1,
            "correct_count": att.correct_count,
            "score": att.total_score,
            "is_sent": "Y" if current_user.sent_at else "N"
        })

    my_memos = UserMemo.query.filter_by(user_id=current_user_id).order_by(UserMemo.created_at.desc()).all()

    return render_template("my_records.html", quiz_results=quiz_results, my_memos=my_memos)


# [API] 메모 수정 처리
@app.route("/api/memo/update/<int:memo_id>", methods=["POST"])
def update_memo_api(memo_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    memo = db.session.get(UserMemo, memo_id)
    if not memo or memo.user_id != session["user_id"]:
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    data = request.get_json()
    new_content = data.get("content", "").strip()

    if not new_content:
        return jsonify({"success": False, "message": "내용을 입력해 주세요."})

    memo.content = new_content
    db.session.commit()
    return jsonify({"success": True, "message": "메모가 성공적으로 수정되었습니다."})


# [API] 메모 삭제 처리
@app.route("/api/memo/delete/<int:memo_id>", methods=["POST"])
def delete_memo_api(memo_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "로그인이 필요합니다."}), 401

    memo = db.session.get(UserMemo, memo_id)
    if not memo or memo.user_id != session["user_id"]:
        return jsonify({"success": False, "message": "권한이 없습니다."}), 403

    db.session.delete(memo)
    db.session.commit()
    return jsonify({"success": True, "message": "메모가 삭제되었습니다."})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)