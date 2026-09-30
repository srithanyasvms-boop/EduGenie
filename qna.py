"""
Question Answering Module for EduGenie.
Answers educational questions using Google Gemini with tutor-like pedagogy.
"""

import logging
from typing import Any, Dict, List
from gemini_client import gemini_client

logger = logging.getLogger("edugenie.qna")

def answer_question(question: str) -> Dict[str, Any]:
    """
    Answers a student's question with educational clarity.

    Args:
        question: The user's question.

    Returns:
        Structured response with the answer.
    """
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    system_instruction = (
        "You are EduGenie, an expert, encouraging, and highly articulate AI tutor. "
        "Your goal is to help students learn effectively. "
        "Follow these rules:\n"
        "1. Answer clearly, accurately, and without unnecessary jargon.\n"
        "2. Break down complex steps logically.\n"
        "3. Include an intuitive real-world example where helpful.\n"
        "4. Use markdown bullet points and formatting to make reading effortless.\n"
        "5. If a question is ambiguous or factually flawed, politely clarify before answering.\n"
        "6. Never hallucinate facts."
    )

    prompt = f"""Student Question: "{cleaned_question}"

Please provide a comprehensive yet concise educational answer. Format your response cleanly using markdown headings, bullet points, and code blocks (if applicable).
Also provide 2-3 relevant follow-up questions the student might want to explore next."""

    answer_text = gemini_client.generate_text(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=0.7
    )

    return {
        "question": cleaned_question,
        "answer": answer_text
    }
