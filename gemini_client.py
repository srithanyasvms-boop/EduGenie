"""
Gemini Client module for EduGenie.
Provides a unified, resilient interface to interact with Google Gemini models.
Uses the current official Google GenAI SDK (google-genai) with support for
gemini-3.5-flash-lite and automatic candidate model fallback.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from config import settings

logger = logging.getLogger("edugenie.gemini")

# Current officially supported Gemini models in prioritized fallback order
CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]


class GeminiClient:
    """Client wrapper for interacting with the Google Gemini API."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        self._client = None
        self._legacy_model = None
        self._sdk_type = None
        self._initialize_client()

    def _initialize_client(self):
        """Initializes the Gemini client using available SDK."""
        if not settings.is_gemini_configured:
            logger.warning("Gemini API key is not configured. AI calls requiring Gemini will return a fallback message.")
            return

        # Attempt 1: Modern google-genai SDK (Official)
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
        Generates text using Google Gemini with automatic model failover across supported models.
        """
        if not settings.is_gemini_configured:
            raise RuntimeError(
                "Gemini API key is not configured. Please add GEMINI_API_KEY to your .env file or Vercel Environment Variables."
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

        # Determine prioritized model list starting with configured model
        models_to_try = [self.model_name] + [m for m in CANDIDATE_MODELS if m != self.model_name]

        last_error = None
        for current_model in models_to_try:
            try:
                # 1. Try modern google-genai SDK
                if self._sdk_type == "google-genai" and self._client:
                    # models.generate_content
                    if hasattr(self._client, "models") and hasattr(self._client.models, "generate_content"):
                        config_kwargs = {}
                        if system_instruction:
                            config_kwargs["system_instruction"] = system_instruction
                        if temperature is not None:
                            config_kwargs["temperature"] = temperature

                        response = self._client.models.generate_content(
                            model=current_model,
                            contents=prompt,
                            config=config_kwargs if config_kwargs else None
                        )
                        if hasattr(response, "text") and response.text:
                            self.model_name = current_model
                            return response.text.strip()
                        elif hasattr(response, "output_text") and response.output_text:
                            self.model_name = current_model
                            return response.output_text.strip()

                    # Interactions API
                    if hasattr(self._client, "interactions") and hasattr(self._client.interactions, "create"):
                        try:
                            interaction = self._client.interactions.create(
                                model=current_model,
                                input=full_prompt
                            )
                            if hasattr(interaction, "output_text") and interaction.output_text:
                                self.model_name = current_model
                                return interaction.output_text.strip()
                        except Exception as inter_err:
                            logger.debug("Interactions API call with %s: %s", current_model, inter_err)

                # 2. Try legacy SDK
                if self._legacy_model:
                    generation_config = {"temperature": temperature}
                    response = self._legacy_model.generate_content(
                        full_prompt,
                        generation_config=generation_config
                    )
                    if response and hasattr(response, "text"):
                        return response.text.strip()

            except Exception as e:
                err_str = str(e).lower()
                last_error = e
                # Check for bad API key immediately
                if "api_key" in err_str or "unauthenticated" in err_str or "401" in err_str:
                    raise RuntimeError("Invalid or expired Gemini API key. Please check GEMINI_API_KEY in your .env or Vercel Environment Variables.")
                
                # For 404 (not found), 429 (rate limited / quota exhausted), or 503 (service unavailable), failover to next model
                if "404" in err_str or "not_found" in err_str or "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "503" in err_str or "unavailable" in err_str:
                    logger.warning("Model %s had issue (%s). Failing over to next supported model...", current_model, e)
                    continue
                else:
                    logger.warning("Error with %s: %s", current_model, e)
                    continue

        logger.error("All Gemini candidate models failed. Last error: %s", last_error)
        raise RuntimeError(f"Gemini API request failed: {str(last_error)}")

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
