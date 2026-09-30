"""
Quiz Generation Module for EduGenie.
Generates structured multiple-choice quizzes with options, answers,
and explanations based on topics or provided source text.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from gemini_client import gemini_client

logger = logging.getLogger("edugenie.quiz")

def generate_quiz(
    topic: str,
    text: str = "",
    number_of_questions: int = 5,
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """
    Generates a structured educational quiz.

    Args:
        topic: Topic for the quiz (e.g. 'Photosynthesis', 'Python Data Structures').
        text: Optional source text to base the quiz questions upon.
        number_of_questions: Number of questions (1-15).
        difficulty: 'easy', 'medium', or 'hard'.

    Returns:
        Structured dictionary containing questions, options, correct answers, and explanations.
    """
    topic = topic.strip()
    if not topic and not text.strip():
        raise ValueError("Either a topic or reference text must be provided to generate a quiz.")

    difficulty = difficulty.lower().strip()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    number_of_questions = max(1, min(15, int(number_of_questions)))

    system_instruction = (
        "You are EduGenie's Quiz Creator. You build fair, accurate, pedagogically sound multiple-choice quizzes. "
        "Every question must have exactly 4 distinct options labeled A, B, C, D (or as a 4-item list). "
        "The correct answer must be unambiguously correct. "
        "Provide a clear explanation for why the correct answer is right and why other options are incorrect."
    )

    source_context = f"Reference Study Material:\n{text.strip()}\n" if text.strip() else ""

    prompt = f"""Create a {difficulty.upper()} multiple-choice quiz with exactly {number_of_questions} questions.
Topic: "{topic}"
{source_context}

Return your response in STRICT JSON format with this exact structure:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": 1,
      "question": "Clear, direct question text here?",
      "options": [
        "Option A text",
        "Option B text",
        "Option C text",
        "Option D text"
      ],
      "correct_answer": "Option A text",
      "explanation": "Detailed explanation of why Option A is correct."
    }}
  ]
}}

CRITICAL RULES:
1. "options" MUST be an array of EXACTLY 4 string choices.
2. "correct_answer" MUST exactly match one of the string choices in "options".
3. Return ONLY valid JSON."""

    try:
        data = gemini_client.generate_json(prompt=prompt, system_instruction=system_instruction)
        
        # Handle variations in JSON structure
        questions_raw = []
        if isinstance(data, dict):
            questions_raw = data.get("questions", [])
            if not questions_raw and "quiz" in data:
                questions_raw = data.get("quiz", [])
        elif isinstance(data, list):
            questions_raw = data

        sanitized_questions = []
        for i, q in enumerate(questions_raw, 1):
            if not isinstance(q, dict):
                continue

            question_text = q.get("question", f"Question {i}")
            options = q.get("options", [])
            correct_ans = q.get("correct_answer", "")
            explanation = q.get("explanation", "Correct understanding of the concept.")

            # Validate options count
            if not isinstance(options, list) or len(options) < 2:
                continue

            # Ensure 4 options
            while len(options) < 4:
                options.append(f"Option {len(options) + 1}")
            options = options[:4]

            # Ensure correct_answer matches an option
            if correct_ans not in options:
                correct_ans = options[0]

            sanitized_questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_ans,
                "explanation": explanation
            })

        if not sanitized_questions:
            raise ValueError("No valid questions could be formatted from the AI response.")

        return {
            "topic": topic or "General Knowledge",
            "difficulty": difficulty,
            "total_questions": len(sanitized_questions),
            "questions": sanitized_questions
        }

    except Exception as e:
        logger.error("Quiz generation error: %s", e, exc_info=True)
        raise RuntimeError(f"Failed to generate quiz: {str(e)}")
