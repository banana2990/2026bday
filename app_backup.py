import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

@app.route("/")
def home():
    return render_template("index.html")


class QuizResult(db.Model):
    __tablename__ = "quiz_result"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)


@app.route("/save-test")
def save_test():
    result = QuizResult(
        username="Yejin",
        score=100
    )

    db.session.add(result)
    db.session.commit()

    return "Saved!"


@app.route("/ranking")
def ranking():

    rankings = QuizResult.query.order_by(
        QuizResult.score.desc()
    ).all()

    return "<br>".join(
        f"{r.username}: {r.score}"
        for r in rankings
    )


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)