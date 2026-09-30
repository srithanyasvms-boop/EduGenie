# EduGenie – Google Gemini Powered Learning Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://python.org)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Powered-4285F4.svg?style=flat&logo=google)](https://aistudio.google.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-LaMini--T5-FFD21E.svg?style=flat&logo=huggingface)](https://huggingface.co/MBZUAI/LaMini-Flan-T5-783M)

**EduGenie** is a full-stack, AI-powered educational assistant engineered to empower students and lifelong learners. It provides instant tutor-level question answering, deep concept explanations across multiple difficulty tiers, textbook and study material summarization, interactive multiple-choice quiz generation with instant scoring, and personalized multi-week learning roadmaps.

---

## 🌟 Core Features

1. **Ask AI Educational Tutor (`/api/ask`)**
   - Step-by-step answers with intuitive analogies, structured bullet points, and follow-up explorations.
   - Built to encourage genuine student comprehension rather than rote answers.

2. **Concept Explainer (`/api/explain`)**
   - Tailors explanations across **Beginner**, **Intermediate**, and **Advanced** tiers.
   - Dual-engine architecture: Uses the lightweight local **LaMini-Flan-T5-783M** model when available, with automatic seamless fallback to **Google Gemini**.

3. **Study Material Summarizer (`/api/summarize`)**
   - Condenses long textbooks, articles, and research passages into high-yield study notes.
   - Computes live stats: original words, summary words, condensation percentage, and reading time saved.

4. **Interactive Quiz Generator (`/api/quiz`)**
   - Generates multiple-choice tests with 4 choices per question, instant score cards, percentage feedback, and detailed answer explanations.
   - Supports quiz generation from general topics or directly from pasted study passages.

5. **Personalized Learning Path (`/api/learning-path`)**
   - Designs structured week-by-week study curricula complete with learning objectives, core topics, hands-on activities, checkpoints, and a capstone project.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Jinja2, python-dotenv
- **AI & LLM**: Google Gemini API (`google-genai` SDK), Hugging Face Transformers (`MBZUAI/LaMini-Flan-T5-783M`), PyTorch
- **Frontend**: HTML5, CSS3 (Modern Glassmorphism & Custom Properties), Vanilla JavaScript (Async/Await Fetch API, zero heavy framework dependencies)
- **Testing**: PyTest, HTTPX, FastAPI TestClient

---

## 📂 Project Structure

```text
EduGenie/
├── main.py                 # FastAPI application, route handlers, exception handling, static mounting
├── config.py               # Centralized configuration & environment loader
├── gemini_client.py        # Resilient Google Gemini SDK client with JSON extraction
├── explanation_module.py   # Concept explainer (LaMini-Flan-T5 local + Gemini fallback)
├── qna.py                  # Question answering module
├── quiz_module.py          # Structured multiple-choice quiz generator
├── summary_module.py       # Study material summarizer with statistics
├── learning_path.py        # Multi-week curriculum roadmap generator
├── requirements.txt        # Full Python dependencies specification
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules for virtualenvs, keys, and caches
├── README.md               # Complete project documentation
│
├── templates/
│   └── index.html          # Modern, responsive single-page educational dashboard
│
├── static/
│   ├── style.css           # Custom modern design, typography, and responsive styles
│   └── script.js           # Interactive state management, API controller, and quiz player
│
├── models/
│   └── README.md           # Documentation for the local LaMini-Flan-T5 model
│
└── tests/
    ├── __init__.py
    └── test_api.py         # Pytest test suite covering endpoints and validation
```

---

## 🚀 Step-by-Step Setup Guide (Windows & VS Code)

### Step 1: Open VS Code Terminal
Open your project folder in VS Code (`File` > `Open Folder...` -> `EduGenie`).
Open the integrated terminal (`Ctrl + ~`).

### Step 2: Create and Activate a Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment on Windows
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Edit `.env` and insert your Gemini API Key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=AIzaSy...your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
HOST=127.0.0.1
PORT=8000
DEBUG=True
USE_LOCAL_MODEL=True
```

### Step 5: Run EduGenie
```powershell
uvicorn main:app --reload
```
or run directly with Python:
```powershell
python main.py
```

Open your browser and navigate to:
- **Web Interface**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Running the Test Suite

Run the full automated test suite with `pytest`:
```powershell
pytest tests/test_api.py -v
```

All API routes, Pydantic validation boundaries, and mocked AI responses are tested automatically without requiring an active API key during test execution.

---

## 📡 API Endpoint Reference

| Method | Endpoint | Description | Sample Request Body |
|---|---|---|---|
| `GET` | `/health` | Service health status | None |
| `GET` | `/` | Web dashboard UI | None |
| `POST` | `/api/ask` | Ask educational question | `{"question": "What is photosynthesis?"}` |
| `POST` | `/api/explain` | Explain concept by level | `{"topic": "Recursion", "level": "beginner"}` |
| `POST` | `/api/summarize` | Summarize study material | `{"text": "Long passage text..."}` |
| `POST` | `/api/quiz` | Generate MC quiz | `{"topic": "Python", "number_of_questions": 5, "difficulty": "medium"}` |
| `POST` | `/api/learning-path` | Multi-week curriculum | `{"topic": "Data Science", "level": "beginner", "duration": "4 weeks", "hours_per_week": 5}` |

---

## 🔒 Security Best Practices

- **Never expose the Gemini API key** in frontend JavaScript or commit it to version control.
- All Gemini API calls are securely performed server-side.
- The `.gitignore` file is preconfigured to ignore `.env`, virtual environments, and downloaded model weights.

---

## 💡 Troubleshooting

- **Gemini API Key Warning**: If you see the yellow banner on the top of the interface, ensure your `.env` contains `GEMINI_API_KEY=your_actual_key` and restart the server.
- **Local Model Download**: The first time you request a concept explanation, `transformers` will download the `MBZUAI/LaMini-Flan-T5-783M` model weights (~3 GB). If you have limited bandwidth or hardware, set `USE_LOCAL_MODEL=False` in `.env` to use Gemini instantly.
