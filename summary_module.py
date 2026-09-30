"""
Summarization Module for EduGenie.
Summarizes long educational passages, preserving essential facts,
definitions, and key takeaways.
"""

import logging
from typing import Any, Dict, List
from gemini_client import gemini_client

logger = logging.getLogger("edugenie.summary")

def summarize_text(text: str) -> Dict[str, Any]:
    """
    Summarizes an educational text passage.

    Args:
        text: The source study material or article text.

    Returns:
        Structured summary containing executive summary, key takeaways,
        and reading statistics.
    """
    cleaned_text = text.strip()
    if not cleaned_text:
        raise ValueError("Text to summarize cannot be empty.")

    if len(cleaned_text) < 20:
        raise ValueError("Text is too short to produce a meaningful summary (minimum 20 characters).")

    # Calculate statistics
    words = cleaned_text.split()
    original_word_count = len(words)
    estimated_read_time_mins = max(1, round(original_word_count / 200))

    system_instruction = (
        "You are EduGenie's Study Summarizer. Your goal is to condense study materials into high-yield, "
        "easy-to-review summaries without losing critical definitions, data, or arguments."
    )

    prompt = f"""Study Passage to Summarize:
{cleaned_text}

Please summarize this study material. Respond in JSON format with the following structure:
{{
  "headline": "A concise title or one-sentence summary of the main theme",
  "summary": "A 2-3 paragraph concise overview capturing the core ideas faithfully",
  "key_points": [
    "Important takeaway 1",
    "Important takeaway 2",
    "Important takeaway 3",
    "Important takeaway 4"
  ],
  "key_terms": [
    {{"term": "Term Name", "definition": "Brief definition from context"}}
  ]
}}"""

    try:
        data = gemini_client.generate_json(prompt=prompt, system_instruction=system_instruction)
        summary_text = data.get("summary", "")
        summary_word_count = len(summary_text.split())
        reduction_percentage = max(0, round((1 - (summary_word_count / max(1, original_word_count))) * 100))

        return {
            "headline": data.get("headline", "Study Summary"),
            "summary": summary_text,
            "key_points": data.get("key_points", []),
            "key_terms": data.get("key_terms", []),
            "stats": {
                "original_words": original_word_count,
                "summary_words": summary_word_count,
                "reduction_percentage": f"{reduction_percentage}%",
                "estimated_read_time_saved": f"{max(0, estimated_read_time_mins - 1)} mins"
            }
        }
    except Exception as e:
        logger.warning("JSON summary generation failed (%s), falling back to text generation.", e)
        raw_summary = gemini_client.generate_text(
            prompt=f"Summarize the following educational text clearly with bullet points:\n\n{cleaned_text}",
            system_instruction=system_instruction
        )
        return {
            "headline": "Study Summary",
            "summary": raw_summary,
            "key_points": ["Review the generated summary points above."],
            "key_terms": [],
            "stats": {
                "original_words": original_word_count,
                "summary_words": len(raw_summary.split()),
                "reduction_percentage": "N/A",
                "estimated_read_time_saved": "1-2 mins"
            }
        }
