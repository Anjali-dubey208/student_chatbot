# Campus Desk — Student Support Chatbot

A student support chatbot with account login and persistent chat history,
built with Flask and the Gemini API.

## What it does

- **Landing page** introducing the chatbot, with a scroll-down section to log in or sign up
- **Signup / login** with hashed passwords (Werkzeug) and session-based auth
- **Chatbot** that answers questions about admissions, exams, fees, courses,
  placements, and general study help — powered by Google's Gemini API
- **Persistent conversation history** — each user's chat is saved to a database
  and restored when they log back in; the bot also uses recent messages as
  context for follow-up questions
- **Clear chat** option to wipe a conversation

## Tech stack

- **Backend:** Flask, Flask-SQLAlchemy
- **Database:** SQLite (file-based, no separate server needed)
- **AI:** Google Gemini API (`google-genai`)
- **Frontend:** Plain HTML/CSS/JS (no framework)

## Project structure

```
student_chatbot/
├── app.py                 # Flask app: routes, models, chat logic
├── requirements.txt
├── .env.example            # copy to .env and fill in your own values
├── static/
│   └── style.css
└── templates/
    ├── landing.html
    ├── login.html
    ├── signup.html
    └── index.html          # the chat page
```

## Setup

1. Clone the repo and move into the project folder:
   ```
   git clone <your-repo-url>
   cd student_chatbot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your own values:
   ```
   cp .env.example .env
   ```
   - `GEMINI_API_KEY` — get one from [Google AI Studio](https://aistudio.google.com/)
   - `SECRET_KEY` — any long random string (used to sign Flask sessions)

4. Run the app:
   ```
   python app.py
   ```

5. Open `http://127.0.0.1:5000` in your browser.

The database (`instance/campus_desk.db`) is created automatically the first
time you run the app.

## Notes

- This is a learning/demo project — the SQLite database is fine for local
  use but isn't set up for production traffic.
- Debug mode (`app.run(debug=True)`) should be turned off before any real
  deployment.
