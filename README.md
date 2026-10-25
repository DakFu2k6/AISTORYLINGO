# ✦ AI StoryLingo

**Learn a language. Live the story.**

AI StoryLingo is a small web app that teaches vocabulary through interactive stories.
You choose a language, level, genre and topic, an AI writes the story, and you learn the new words while you read, make choices that change the plot, and finish with a quiz.

> Course project: Web Design & Programming · runs fully on `localhost`

## What you can do

1. **Create an account / log in**
2. **Generate a story** from language, level, genre, topic and number of words
3. **Read** it: new words are highlighted. Click a word to see its pronunciation, meaning, Vietnamese meaning and an example, listen to it, and save it to your notebook
4. **Choose** what happens next (A / B / C). The AI writes the next chapter from your choice
5. **Take a quiz** on the words of the story. Your mastery of each word goes up or down
6. **See your progress**: stories, saved words, mastery bars, quiz accuracy, and open old stories again

## Tech stack

| Part | Technology |
|---|---|
| Frontend | HTML, CSS, vanilla JavaScript (no build step) |
| Backend | Python, FastAPI |
| Database | SQLite (via SQLModel); can switch to PostgreSQL with one setting |
| AI | Google Gemini API (optional, a demo story is built in) |
| Speech | Browser Web Speech API |

## Project structure

```
AI-StoryLingo/
├── README.md
├── .env.example            # copy to backend/.env
├── .gitignore
├── docs/
│   └── ARCHITECTURE.md     # diagrams, database tables, API list
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py         # starts the API
│   │   ├── database.py     # database connection
│   │   ├── models.py       # database tables
│   │   ├── serializers.py  # database row -> JSON
│   │   ├── routes/         # auth, stories, vocabulary, quiz, dashboard
│   │   └── services/       # story_service.py (Gemini) + demo_story.py
│   ├── ai_engine/          # prompts.py + schemas.py (what we ask the AI)
│   └── tests/              # automatic test of the whole flow
└── frontend/
    ├── index.html          # all screens
    ├── style.css           # all styling
    ├── api.js              # every call to the backend
    └── app.js              # screens and buttons
```

## How to run (localhost)

You need **Python 3.10+**. Open **two terminals** in the project folder.

**Terminal 1: backend**

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Mac / Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at http://localhost:8000 and its documentation at http://localhost:8000/docs.
The database file `backend/storylingo.db` is created automatically.

**Terminal 2: frontend**

```bash
cd frontend
python -m http.server 3000
```

Open **http://localhost:3000** in your browser.

### Using the real AI (optional)

Without a key the app still works: it shows a built-in demo story (marked with a **Demo story** badge).
To use Gemini:

1. Get a free key at https://aistudio.google.com/apikey
2. Copy `.env.example` to `backend/.env` and write your key: `GEMINI_API_KEY=your_key`
3. Restart the backend

If Google changes model names, set `GEMINI_MODEL` in the same file. If the AI call fails during use, the app falls back to the demo text instead of crashing.

### Run the automatic test

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -v
```

## Demo script (3 minutes)

1. Create an account
2. Choose English · B1 · Fantasy · topic "space" · 5 words → **Generate story**
3. Click a highlighted word → listen → **Save word**
4. Pick choice **A** → chapter 2 appears → pick again → chapter 3 and **The End**
5. **Take the quiz** → answer 5 questions
6. Open **Progress** → show stats, mastery bars, and **Read again**

## Team

| Member | Main work |
|---|---|
| Member 1 (name) | Frontend: screens, popup, quiz and progress UI |
| Member 2 (name) | Backend and database: API, models, tests |
| Member 3 (name) | AI and docs: prompts, story service, README, diagrams |

All members review each other's Pull Requests.

## Git workflow

- `main` always works. Nobody pushes to it directly.
- One branch per task: `feature/story-reader`, `feature/quiz`, `fix/login-error`
- Open a Pull Request, another member reviews and merges
- Commit messages: `feat: add choice buttons`, `fix: handle empty topic`, `docs: update README`

## Limitations (known, on purpose)

- Login is simplified for a class demo: passwords are hashed with bcrypt, but there are no tokens/sessions, so it is **not** production security
- The demo story is fixed text and ignores the topic you type
- Only English, Japanese and Korean are offered; the quiz asks for meanings (not fill-in-the-blank)
