from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from dotenv import load_dotenv
from datetime import datetime
import os
import markdown

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///campus_desk.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------- Models ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship(
        "Message", backref="user", lazy=True, cascade="all, delete-orphan"
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # "user" or "bot"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# ---------- Helpers ----------
def current_user():
    username = session.get("username")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


# ---------- Landing page ----------
@app.route("/")
def landing():
    if "username" in session:
        return redirect(url_for("chat_page"))
    return render_template("landing.html")


# ---------- Signup ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            return render_template("signup.html", error="Please fill in all fields.")

        if User.query.filter_by(username=username).first():
            return render_template("signup.html", error="That username is already taken.")

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        session["username"] = username
        return redirect(url_for("chat_page"))

    return render_template("signup.html")


# ---------- Login ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return render_template("login.html", error="Incorrect username or password.")

        session["username"] = username
        return redirect(url_for("chat_page"))

    return render_template("login.html")


# ---------- Logout ----------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("landing"))


# ---------- Chat page (protected) ----------
@app.route("/chatbot")
def chat_page():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    history = (
        Message.query.filter_by(user_id=user.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return render_template("index.html", username=user.username, history=history)


# ---------- Chat API (protected) ----------
@app.route("/chat", methods=["POST"])
def chat():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    user_message = request.json["message"]

    # pull recent history so the bot has context
    recent = (
        Message.query.filter_by(user_id=user.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    recent.reverse()

    convo_text = ""
    for turn in recent:
        speaker = "Student" if turn.role == "user" else "Assistant"
        convo_text += f"{speaker}: {turn.content}\n"

    prompt = f"""
    You are a Student Support Chatbot.

    Answer questions related to:
    - Admissions
    - Exams
    - Fees
    - Courses
    - Placements
    - General study help

    Use the conversation so far for context if relevant.

    Conversation so far:
    {convo_text}

    New question:
    {user_message}
    """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    html_response = markdown.markdown(response.text)

    db.session.add(Message(user_id=user.id, role="user", content=user_message))
    db.session.add(Message(user_id=user.id, role="bot", content=html_response))
    db.session.commit()

    return jsonify({"reply": html_response})


# ---------- Clear conversation (protected) ----------
@app.route("/chat/clear", methods=["POST"])
def clear_chat():
    user = current_user()
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    Message.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    app.run(debug=True)
