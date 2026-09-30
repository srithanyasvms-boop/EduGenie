"""
Comprehensive Test Suite for EduGenie FastAPI Application.
Tests health check, UI template delivery, request validation,
and mock AI endpoints without requiring a live Gemini API key.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test GET /health returns 200 and healthy service metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "EduGenie"
    assert "version" in data


def test_get_index():
    """Test GET / returns HTML homepage."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "EduGenie" in response.text


# ---------------------------------------------------------------------
# Validation Error Tests (Testing Pydantic Schema Contracts)
# ---------------------------------------------------------------------

def test_ask_validation_empty():
    """Test POST /api/ask rejects empty question."""
    response = client.post("/api/ask", json={"question": "   "})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_explain_validation_invalid_level():
    """Test POST /api/explain rejects unsupported difficulty level."""
    response = client.post("/api/explain", json={"topic": "Python", "level": "super-hard"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


def test_summarize_validation_too_short():
    """Test POST /api/summarize rejects text shorter than 20 chars."""
    response = client.post("/api/summarize", json={"text": "Too short"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


def test_quiz_validation_bounds():
    """Test POST /api/quiz rejects invalid number of questions (>15)."""
    response = client.post("/api/quiz", json={"topic": "Physics", "number_of_questions": 50})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


def test_learning_path_validation_empty_topic():
    """Test POST /api/learning-path rejects empty topic."""
    response = client.post("/api/learning-path", json={"topic": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


# ---------------------------------------------------------------------
# Mocked AI Generation Tests (Mocking AI responses for testing)
# ---------------------------------------------------------------------

@patch("qna.gemini_client.generate_text")
def test_mock_ask_success(mock_gemini):
    """Test POST /api/ask with mocked Gemini response."""
    mock_gemini.return_value = "Photosynthesis is the process of converting light to sugar."
    response = client.post("/api/ask", json={"question": "What is photosynthesis?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Photosynthesis" in data["data"]["answer"]


@patch("explanation_module.gemini_client.generate_json")
def test_mock_explain_gemini_success(mock_json):
    """Test POST /api/explain with mocked structured explanation."""
    mock_json.return_value = {
        "definition": "Recursion is a function calling itself.",
        "explanation": "A recursive function has a base case and recursive step.",
        "example": "Russian nesting dolls.",
        "key_takeaways": ["Base case prevents infinite loops", "Uses stack memory"]
    }
    response = client.post("/api/explain", json={"topic": "Recursion", "level": "beginner"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["topic"] == "Recursion"
    assert data["data"]["definition"] == "Recursion is a function calling itself."


@patch("summary_module.gemini_client.generate_json")
def test_mock_summarize_success(mock_json):
    """Test POST /api/summarize with mocked summary."""
    mock_json.return_value = {
        "headline": "Overview of AI",
        "summary": "Artificial Intelligence enables computers to learn from data.",
        "key_points": ["Machine learning is a subset of AI", "Deep learning uses neural networks"],
        "key_terms": [{"term": "AI", "definition": "Artificial Intelligence"}]
    }
    sample_text = "Artificial Intelligence represents the simulation of human intelligence by machines and computer systems."
    response = client.post("/api/summarize", json={"text": sample_text})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["headline"] == "Overview of AI"


@patch("quiz_module.gemini_client.generate_json")
def test_mock_quiz_success(mock_json):
    """Test POST /api/quiz with mocked structured questions."""
    mock_json.return_value = {
        "topic": "Python",
        "difficulty": "medium",
        "questions": [
            {
                "id": 1,
                "question": "Which keyword defines a function in Python?",
                "options": ["def", "func", "function", "lambda"],
                "correct_answer": "def",
                "explanation": "'def' is the reserved keyword in Python for function definition."
            }
        ]
    }
    response = client.post("/api/quiz", json={"topic": "Python", "number_of_questions": 1, "difficulty": "medium"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_questions"] == 1
    assert data["data"]["questions"][0]["correct_answer"] == "def"


@patch("learning_path.gemini_client.generate_json")
def test_mock_learning_path_success(mock_json):
    """Test POST /api/learning-path with mocked curriculum."""
    mock_json.return_value = {
        "title": "Mastering Python in 4 Weeks",
        "overview": "A step-by-step roadmap to Python mastery.",
        "prerequisites": ["Basic computer literacy"],
        "weekly_plan": [
            {
                "week": 1,
                "title": "Python Fundamentals",
                "learning_goals": ["Variables and Data Types"],
                "core_topics": ["Strings", "Lists", "Loops"],
                "activities": ["Build a CLI calculator"],
                "practice_tasks": ["5 coding problems"],
                "checkpoint": "Write a clean CLI script"
            }
        ],
        "capstone_project": {
            "title": "Data Analysis Dashboard",
            "description": "Build an end-to-end Python app."
        },
        "recommended_resources": ["Python.org docs"]
    }
    response = client.post("/api/learning-path", json={
        "topic": "Python Programming",
        "level": "beginner",
        "duration": "4 weeks",
        "hours_per_week": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Python" in data["data"]["title"]
    assert len(data["data"]["weekly_plan"]) == 1
