"""
Main FastAPI Application for EduGenie.
Configures routes, static files, Jinja2 templates, request validation,
exception handlers, and CORS.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from config import settings
from explanation_module import explain_concept
from learning_path import generate_learning_path
from qna import answer_question
from quiz_module import generate_quiz
from summary_module import summarize_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("edugenie.main")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local development and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates configuration
BASE_DIR = Path(__file__).resolve().parent
templates_dir = BASE_DIR / "templates"
static_dir = BASE_DIR / "static"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ---------------------------------------------------------------------
# Pydantic Request Models with Rich Validation
# ---------------------------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        description="The educational question asked by the student.",
        min_length=3,
        max_length=2000,
        examples=["What is the difference between supervised and unsupervised learning?"]
    )

    @field_validator("question")
    @classmethod
    def validate_question_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Question cannot be empty or just whitespace.")
        return clean


class ExplainRequest(BaseModel):
    topic: str = Field(
        ...,
        description="The concept or topic to be explained.",
        min_length=2,
        max_length=300,
        examples=["Photosynthesis", "Recursion", "Quantum Entanglement"]
    )
    level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        description="Target student depth level."
    )

    @field_validator("topic")
    @classmethod
    def validate_topic_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Topic cannot be empty or just whitespace.")
        return clean


class SummaryRequest(BaseModel):
    text: str = Field(
        ...,
        description="Long educational passage to summarize.",
        min_length=20,
        max_length=100000,
        examples=["Artificial Intelligence is a branch of computer science..."]
    )

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 20:
            raise ValueError("Text must contain at least 20 characters for a meaningful summary.")
        return clean


class QuizRequest(BaseModel):
    topic: str = Field(
        default="",
        description="The topic to generate questions for.",
        max_length=300,
        examples=["Python Basics", "Cell Biology"]
    )
    text: Optional[str] = Field(
        default="",
        description="Optional study text to base the quiz upon.",
        max_length=100000
    )
    number_of_questions: int = Field(
        default=5,
        ge=1,
        le=15,
        description="Number of multiple choice questions (1-15)."
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="Difficulty level of the quiz."
    )

    @field_validator("topic")
    @classmethod
    def validate_quiz_inputs(cls, v: str) -> str:
        return v.strip()


class LearningPathRequest(BaseModel):
    topic: str = Field(
        ...,
        description="The subject or skill to build a roadmap for.",
        min_length=2,
        max_length=300,
        examples=["Full Stack Web Development", "Machine Learning"]
    )
    level: Literal["beginner", "intermediate", "advanced"] = Field(
        default="beginner",
        description="Current learner level."
    )
    duration: str = Field(
        default="4 weeks",
        description="Target duration (e.g. '2 weeks', '4 weeks', '8 weeks', '12 weeks').",
        max_length=50
    )
    hours_per_week: int = Field(
        default=5,
        ge=1,
        le=40,
        description="Weekly study hours commitment."
    )

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Topic cannot be empty.")
        return clean


# ---------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors into standardized JSON error responses."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid input")
        errors.append(f"{field}: {msg}")
    
    error_msg = "; ".join(errors) if errors else "Invalid request data."
    logger.warning("Validation error on %s: %s", request.url.path, error_msg)
    
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": error_msg}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTP exceptions into standardized JSON error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global catch-all for uncaught exceptions."""
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected server error occurred. Please verify your Gemini API key and try again."
        }
    )


# ---------------------------------------------------------------------
# Frontend and Health Endpoints
# ---------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, summary="EduGenie Web Dashboard")
async def get_index(request: Request):
    """Renders the main EduGenie single-page web interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_title": settings.APP_TITLE,
            "app_name": settings.APP_NAME,
            "gemini_configured": settings.is_gemini_configured,
            "gemini_model": settings.GEMINI_MODEL,
            "use_local_model": settings.USE_LOCAL_MODEL,
        }
    )


@app.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "gemini_configured": settings.is_gemini_configured,
        "gemini_model": settings.GEMINI_MODEL,
        "local_model_enabled": settings.USE_LOCAL_MODEL
    }


# ---------------------------------------------------------------------
# AI REST API Endpoints
# ---------------------------------------------------------------------

@app.post("/api/ask", summary="Ask an Educational Question")
async def api_ask_question(payload: AskRequest):
    """
    Answers an educational question using Google Gemini with tutor-guided pedagogy.
    """
    try:
        data = answer_question(payload.question)
        return {"success": True, "data": data}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"success": False, "error": str(ve)})
    except RuntimeError as re:
        return JSONResponse(status_code=503, content={"success": False, "error": str(re)})
    except Exception as e:
        logger.error("Error in /api/ask: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to answer question: {str(e)}"}
        )


@app.post("/api/explain", summary="Explain an Educational Concept")
async def api_explain_concept(payload: ExplainRequest):
    """
    Explains an educational concept at the selected difficulty level.
    Uses local model (LaMini-Flan-T5) if available, with automatic fallback to Gemini.
    """
    try:
        data = explain_concept(payload.topic, payload.level)
        return {"success": True, "data": data}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"success": False, "error": str(ve)})
    except RuntimeError as re:
        return JSONResponse(status_code=503, content={"success": False, "error": str(re)})
    except Exception as e:
        logger.error("Error in /api/explain: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to explain concept: {str(e)}"}
        )


@app.post("/api/summarize", summary="Summarize Study Material")
async def api_summarize_text(payload: SummaryRequest):
    """
    Summarizes long educational text, extracting core themes, key takeaways, and definitions.
    """
    try:
        data = summarize_text(payload.text)
        return {"success": True, "data": data}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"success": False, "error": str(ve)})
    except RuntimeError as re:
        return JSONResponse(status_code=503, content={"success": False, "error": str(re)})
    except Exception as e:
        logger.error("Error in /api/summarize: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to summarize text: {str(e)}"}
        )


@app.post("/api/quiz", summary="Generate an Educational Quiz")
async def api_generate_quiz(payload: QuizRequest):
    """
    Generates an interactive multiple-choice quiz from a topic or study passage.
    """
    try:
        if not payload.topic and not payload.text:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Please provide either a topic or study text to generate a quiz."}
            )
        data = generate_quiz(
            topic=payload.topic,
            text=payload.text or "",
            number_of_questions=payload.number_of_questions,
            difficulty=payload.difficulty
        )
        return {"success": True, "data": data}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"success": False, "error": str(ve)})
    except RuntimeError as re:
        return JSONResponse(status_code=503, content={"success": False, "error": str(re)})
    except Exception as e:
        logger.error("Error in /api/quiz: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to generate quiz: {str(e)}"}
        )


@app.post("/api/learning-path", summary="Generate a Personalized Learning Path")
async def api_learning_path(payload: LearningPathRequest):
    """
    Generates a personalized multi-week learning curriculum tailored to the student's goals.
    """
    try:
        data = generate_learning_path(
            topic=payload.topic,
            level=payload.level,
            duration=payload.duration,
            hours_per_week=payload.hours_per_week
        )
        return {"success": True, "data": data}
    except ValueError as ve:
        return JSONResponse(status_code=400, content={"success": False, "error": str(ve)})
    except RuntimeError as re:
        return JSONResponse(status_code=503, content={"success": False, "error": str(re)})
    except Exception as e:
        logger.error("Error in /api/learning-path: %s", e, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Failed to generate learning path: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    print(f"Starting {settings.APP_TITLE} on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
