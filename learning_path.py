"""
Learning Path Generation Module for EduGenie.
Generates structured, personalized multi-week learning roadmaps
complete with weekly concepts, hands-on tasks, practice, and checkpoints.
"""

import logging
from typing import Any, Dict, List
from gemini_client import gemini_client

logger = logging.getLogger("edugenie.learning_path")

def generate_learning_path(
    topic: str,
    level: str = "beginner",
    duration: str = "4 weeks",
    hours_per_week: int = 5
) -> Dict[str, Any]:
    """
    Generates a personalized educational learning path.

    Args:
        topic: The topic or skill to master (e.g. 'Python for Data Science', 'Quantum Physics').
        level: Current skill level ('beginner', 'intermediate', 'advanced').
        duration: Target timeframe (e.g. '2 weeks', '4 weeks', '8 weeks', '12 weeks').
        hours_per_week: Weekly time commitment in hours.

    Returns:
        Structured curriculum with weekly milestones, activities, and projects.
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("Topic cannot be empty.")

    level = level.lower().strip()
    if level not in ("beginner", "intermediate", "advanced"):
        level = "beginner"

    duration = duration.strip() or "4 weeks"
    hours_per_week = max(1, min(40, int(hours_per_week)))

    system_instruction = (
        "You are EduGenie's Curriculum Architect. You design realistic, highly engaging, "
        "and outcome-oriented learning roadmaps tailored to a student's available time and starting level."
    )

    prompt = f"""Design a comprehensive, structured learning roadmap for:
Topic: "{topic}"
Starting Level: {level.capitalize()}
Total Duration: {duration}
Study Commitment: {hours_per_week} hours per week

Respond in JSON with this exact structure:
{{
  "title": "Mastering {topic}: A {duration} Journey",
  "overview": "A 2-3 sentence motivating summary of what the learner will achieve.",
  "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
  "weekly_plan": [
    {{
      "week": 1,
      "title": "Week 1 Theme/Title",
      "learning_goals": [
        "Goal 1",
        "Goal 2"
      ],
      "core_topics": [
        "Topic 1",
        "Topic 2",
        "Topic 3"
      ],
      "activities": [
        "Hands-on activity 1",
        "Hands-on activity 2"
      ],
      "practice_tasks": [
        "Coding or writing exercise 1",
        "Self-test exercise 2"
      ],
      "checkpoint": "How to verify mastery before moving to the next week"
    }}
  ],
  "capstone_project": {{
    "title": "Final Project Title",
    "description": "A comprehensive project demonstrating mastery of all concepts learned."
  }},
  "recommended_resources": [
    "Recommended book, doc, or tutorial 1",
    "Recommended tool or platform 2"
  ]
}}

CRITICAL: Return ONLY valid JSON. Provide a plan that matches the requested duration."""

    try:
        data = gemini_client.generate_json(prompt=prompt, system_instruction=system_instruction)
        
        # Ensure fallback defaults if keys missing
        title = data.get("title", f"Learning Path: {topic}")
        overview = data.get("overview", f"A personalized curriculum to master {topic}.")
        prereqs = data.get("prerequisites", ["Curiosity and dedication to learn"])
        weekly_plan = data.get("weekly_plan", [])
        capstone = data.get("capstone_project", {
            "title": f"Complete {topic} Portfolio Project",
            "description": "Build a real-world application or comprehensive case study."
        })
        resources = data.get("recommended_resources", ["Official Documentation", "Interactive Practice Platforms"])

        return {
            "topic": topic,
            "level": level,
            "duration": duration,
            "hours_per_week": hours_per_week,
            "title": title,
            "overview": overview,
            "prerequisites": prereqs,
            "weekly_plan": weekly_plan,
            "capstone_project": capstone,
            "recommended_resources": resources
        }
    except Exception as e:
        logger.error("Learning path generation error: %s", e, exc_info=True)
        raise RuntimeError(f"Failed to generate learning path: {str(e)}")
