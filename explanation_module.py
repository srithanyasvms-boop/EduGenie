"""
Concept Explanation Module for EduGenie.
Uses the local lightweight model (MBZUAI/LaMini-Flan-T5-783M) when available,
with a seamless, graceful fallback to Google Gemini when local ML dependencies
or hardware are unavailable.
"""

import logging
import threading
from typing import Any, Dict, List, Optional
from config import settings
from gemini_client import gemini_client

logger = logging.getLogger("edugenie.explain")

class ConceptExplainer:
    """Explains educational concepts tailored by level with local + cloud fallback."""

    def __init__(self):
        self._local_pipeline = None
        self._load_lock = threading.Lock()
        self._load_attempted = False
        self._local_available = False

    def _get_local_pipeline(self):
        """
        Lazily loads the local HuggingFace LaMini-Flan-T5 model.
        Thread-safe singleton pattern.
        """
        if not settings.USE_LOCAL_MODEL:
            return None

        if self._load_attempted:
            return self._local_pipeline

        with self._load_lock:
            if self._load_attempted:
                return self._local_pipeline

            self._load_attempted = True
            logger.info("Attempting to load local model: %s...", settings.LOCAL_MODEL_NAME)
            
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
                
                device = 0 if torch.cuda.is_available() else -1
                tokenizer = AutoTokenizer.from_pretrained(
                    settings.LOCAL_MODEL_NAME,
                    cache_dir=settings.LOCAL_MODEL_CACHE_DIR
                )
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    settings.LOCAL_MODEL_NAME,
                    cache_dir=settings.LOCAL_MODEL_CACHE_DIR
                )
                
                self._local_pipeline = pipeline(
                    "text2text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_length=512,
                    device=device
                )
                self._local_available = True
                logger.info("Successfully loaded local LaMini-Flan-T5 model!")
            except Exception as e:
                logger.warning(
                    "Local model '%s' could not be loaded (%s). "
                    "EduGenie will use Google Gemini as an automatic fallback.",
                    settings.LOCAL_MODEL_NAME, e
                )
                self._local_pipeline = None
                self._local_available = False

        return self._local_pipeline

    def explain_concept(self, topic: str, level: str = "beginner") -> Dict[str, Any]:
        """
        Explains an educational concept.

        Args:
            topic: The educational concept or topic (e.g. 'Photosynthesis', 'Recursion').
            level: 'beginner', 'intermediate', or 'advanced'.

        Returns:
            Structured dictionary with definition, explanation, example, key points, and metadata.
        """
        topic = topic.strip()
        if not topic:
            raise ValueError("Topic cannot be empty.")

        level = level.lower().strip()
        if level not in ("beginner", "intermediate", "advanced"):
            level = "beginner"

        # Try local model first if configured
        local_pipe = self._get_local_pipeline()
        if local_pipe:
            try:
                return self._explain_with_local_model(local_pipe, topic, level)
            except Exception as e:
                logger.warning("Local model generation failed: %s. Falling back to Gemini.", e)

        # Fallback to Gemini
        return self._explain_with_gemini(topic, level)

    def _explain_with_local_model(self, pipe, topic: str, level: str) -> Dict[str, Any]:
        """Generates explanation using the local LaMini-Flan-T5 model."""
        prompt = (
            f"Explain the concept of '{topic}' for a {level} student. "
            f"Provide a clear definition, a simple explanation, a real-world example, and key takeaways."
        )
        output = pipe(prompt, max_length=512, do_sample=True, temperature=0.7)
        generated_text = output[0]["generated_text"].strip() if output else ""

        return {
            "topic": topic,
            "level": level,
            "engine": "local_lamini",
            "model_name": settings.LOCAL_MODEL_NAME,
            "definition": f"{topic} is an important concept in learning.",
            "explanation": generated_text,
            "example": f"Think of {topic} in everyday life context.",
            "key_takeaways": [
                f"Core foundation of {topic}",
                f"Applicable in practical scenarios",
                f"Mastered through consistent practice"
            ],
            "full_text": generated_text
        }

    def _explain_with_gemini(self, topic: str, level: str) -> Dict[str, Any]:
        """Generates high-quality structured explanation using Google Gemini."""
        system_instruction = (
            "You are EduGenie, an exceptional educational tutor. "
            "Your mission is to explain complex topics with clarity, accuracy, and engaging pedagogy. "
            "Adapt your vocabulary and depth precisely to the requested student level."
        )

        level_guidance = {
            "beginner": "Use simple analogies, everyday language, no heavy jargon, and intuitive metaphors.",
            "intermediate": "Introduce standard terminology, explain underlying mechanisms, and connect concepts.",
            "advanced": "Provide deep technical precision, architectural/mathematical nuances, trade-offs, and edge cases."
        }.get(level, "beginner")

        prompt = f"""Please explain the educational concept: "{topic}"
Target Student Level: {level.capitalize()} ({level_guidance})

Provide your response in JSON format with exactly this structure:
{{
  "definition": "A crisp, 1-2 sentence core definition.",
  "explanation": "A detailed, step-by-step educational breakdown suited for the {level} level.",
  "example": "A memorable real-world analogy or practical example illustrating the concept.",
  "key_takeaways": [
    "Key takeaway point 1",
    "Key takeaway point 2",
    "Key takeaway point 3"
  ]
}}"""

        try:
            data = gemini_client.generate_json(prompt=prompt, system_instruction=system_instruction)
            
            # Extract fields with safe defaults
            definition = data.get("definition", f"{topic} definition.")
            explanation = data.get("explanation", "")
            example = data.get("example", "")
            takeaways = data.get("key_takeaways", [])
            if not isinstance(takeaways, list):
                takeaways = [str(takeaways)]

            full_text = f"**Definition:**\n{definition}\n\n**Explanation:**\n{explanation}\n\n**Example:**\n{example}"

            return {
                "topic": topic,
                "level": level,
                "engine": "gemini",
                "model_name": settings.GEMINI_MODEL,
                "definition": definition,
                "explanation": explanation,
                "example": example,
                "key_takeaways": takeaways,
                "full_text": full_text
            }
        except Exception as e:
            # Fallback to plain text if JSON extraction failed
            raw_text = gemini_client.generate_text(
                prompt=f"Explain {topic} for a {level} student in simple, clear educational terms with examples.",
                system_instruction=system_instruction
            )
            return {
                "topic": topic,
                "level": level,
                "engine": "gemini",
                "model_name": settings.GEMINI_MODEL,
                "definition": f"Core concept: {topic}",
                "explanation": raw_text,
                "example": "Refer to the explanation above for examples.",
                "key_takeaways": ["Understand the core principles", "Review the practical applications"],
                "full_text": raw_text
            }


# Singleton instance
concept_explainer = ConceptExplainer()

def explain_concept(topic: str, level: str = "beginner") -> Dict[str, Any]:
    """Helper function for concept explanation."""
    return concept_explainer.explain_concept(topic=topic, level=level)
