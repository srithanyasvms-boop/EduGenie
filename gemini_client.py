"""
Gemini Client module for EduGenie.
Provides a unified, resilient interface to interact with Google Gemini models.
Uses the official Google GenAI SDK with graceful fallbacks.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from config import settings

logger = logging.getLogger("edugenie.gemini")

class GeminiClient:
    """Client wrapper for interacting with the Google Gemini API."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        self._legacy_model = None
        self._sdk_type = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Gemini client using available SDK."""
        if not settings.is_gemini_configured:
            logger.warning("Gemini API key is not configured. AI calls requiring Gemini will return a fallback message.")
            return

        # Attempt 1: Modern google-genai SDK
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            self._sdk_type = "google-genai"
            logger.info("Initialized modern google-genai SDK with model: %s", self.model_name)
            return
        except ImportError:
            logger.info("google-genai SDK not found, checking for google-generativeai SDK...")
        except Exception as e:
            logger.warning("Error initializing google-genai client: %s", e)

        # Attempt 2: google.generativeai SDK (compatibility fallback)
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self._legacy_model = genai_legacy.GenerativeModel(self.model_name)
            self._sdk_type = "google-generativeai"
            logger.info("Initialized google.generativeai SDK with model: %s", self.model_name)
            return
        except ImportError:
            logger.warning("Neither google-genai nor google-generativeai is installed.")
        except Exception as e:
            logger.warning("Error configuring google.generativeai: %s", e)

    def is_configured(self) -> bool:
        """Returns True if the client is properly configured with an API key."""
        return settings.is_gemini_configured and (self._client is not None or self._legacy_model is not None)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generates text using Google Gemini.

        Args:
            prompt: The user prompt or instruction.
            system_instruction: Optional system instruction for personality and constraints.
            temperature: Creativity control parameter (0.0 - 1.0).

        Returns:
            The generated text response.
        """
        if not settings.is_gemini_configured:
            raise RuntimeError(
                "Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file."
            )

        if not self.is_configured():
            self._initialize_client()
            if not self.is_configured():
                raise RuntimeError(
                    "Unable to initialize Gemini SDK. Please ensure 'google-genai' is installed and your API key is valid."
                )

        full_prompt = prompt
        if system_instruction:
            full_prompt = f"System Instructions: {system_instruction}\n\nTask:\n{prompt}"

        try:
            # 1. Modern SDK
            if self._sdk_type == "google-genai" and self._client:
                if hasattr(self._client, "models") and hasattr(self._client.models, "generate_content"):
                    config_kwargs = {}
                    if system_instruction:
                        config_kwargs["system_instruction"] = system_instruction
                    if temperature is not None:
                        config_kwargs["temperature"] = temperature
                        
                    response = self._client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config_kwargs if config_kwargs else None
                    )
                    if hasattr(response, "text") and response.text:
                        return response.text.strip()
                    elif hasattr(response, "output_text") and response.output_text:
                        return response.output_text.strip()

                if hasattr(self._client, "interactions") and hasattr(self._client.interactions, "create"):
                    interaction = self._client.interactions.create(
                        model=self.model_name,
                        input=full_prompt
                    )
                    if hasattr(interaction, "output_text") and interaction.output_text:
                        return interaction.output_text.strip()

            # 2. Legacy SDK
            if self._legacy_model:
                generation_config = {"temperature": temperature}
                response = self._legacy_model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                if response and hasattr(response, "text"):
                    return response.text.strip()

            raise RuntimeError("Received empty or incompatible response from Gemini API.")

        except Exception as e:
            logger.error("Gemini API generation error: %s", e, exc_info=True)
            error_str = str(e).lower()
            if "api_key" in error_str or "unauthenticated" in error_str or "401" in error_str:
                raise RuntimeError("Invalid or expired Gemini API key. Please check your GEMINI_API_KEY in .env.")
            elif "quota" in error_str or "429" in error_str or "resource_exhausted" in error_str:
                raise RuntimeError("Gemini API rate limit or quota exceeded. Please try again in a moment.")
            else:
                raise RuntimeError(f"Gemini API request failed: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Generates structured JSON data from Gemini with robust sanitization and parsing.
        """
        json_instruction = (
            (system_instruction + "\n" if system_instruction else "")
            + "CRITICAL: You MUST respond ONLY with valid, raw JSON (no preamble, no conversational text, no markdown codeblocks outside of valid JSON)."
        )
        raw_text = self.generate_text(prompt=prompt, system_instruction=json_instruction, temperature=0.3)
        return self._extract_json(raw_text)

    @staticmethod
    def _extract_json(text: str) -> Union[Dict[str, Any], List[Any]]:
        """Extracts and parses JSON from potentially noisy model output."""
        cleaned = text.strip()
        
        # 1. Direct JSON parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 2. Extract from markdown code blocks
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                cleaned = fence_match.group(1).strip()

        # 3. Extract bracketed array [...]
        array_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", cleaned)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        # 4. Extract curly bracket object {...}
        object_match = re.search(r"\{[\s\S]*\}", cleaned)
        if object_match:
            try:
                return json.loads(object_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse valid JSON from AI response: {text[:200]}...")


# Singleton instance
gemini_client = GeminiClient()
