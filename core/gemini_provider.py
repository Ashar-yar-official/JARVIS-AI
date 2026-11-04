
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from core.ai_engine import (
    AIProvider,
    ProviderNotConfiguredError,
    THINKING_LOW,
    THINKING_MEDIUM,
    THINKING_HIGH
)


load_dotenv()


class GeminiProvider(AIProvider):

    def __init__(self, model="gemini-3.5-flash-lite"):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ProviderNotConfiguredError(
                "Gemini API key was not found. "
                "Check the project's .env file."
            )

        self.model = model

        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=90000,
                retry_options=types.HttpRetryOptions(
                    attempts=2
                )
            )
        )

    # =====================================================
    # BUILD REQUEST CONFIGURATION
    # =====================================================

    def build_config(
        self,
        system_instruction,
        thinking_level
    ):

        allowed_levels = (
            THINKING_LOW,
            THINKING_MEDIUM,
            THINKING_HIGH
        )

        if thinking_level not in allowed_levels:
            thinking_level = THINKING_MEDIUM

        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            thinking_config=types.ThinkingConfig(
                thinking_level=thinking_level
            ),
            max_output_tokens=1024
        )

    # =====================================================
    # CONVERT MESSAGES
    # =====================================================

    @staticmethod
    def prepare_contents(messages):

        contents = []

        for message in messages:

            role = message.get("role")
            content = message.get("content", "")

            if role not in ("user", "assistant"):
                continue

            if not isinstance(content, str) or not content.strip():
                continue

            gemini_role = (
                "model" if role == "assistant" else "user"
            )

            contents.append(
                types.Content(
                    role=gemini_role,
                    parts=[
                        types.Part.from_text(text=content)
                    ]
                )
            )

        if not contents:
            raise ValueError(
                "No valid conversation messages supplied."
            )

        return contents

    # =====================================================
    # NORMAL RESPONSE
    # =====================================================

    def generate_response(
        self,
        messages,
        system_instruction,
        thinking_level=THINKING_MEDIUM
    ):

        contents = self.prepare_contents(messages)

        config = self.build_config(
            system_instruction,
            thinking_level
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )

        return response.text or ""

    # =====================================================
    # STREAMING RESPONSE
    # =====================================================

    def generate_response_stream(
        self,
        messages,
        system_instruction,
        thinking_level=THINKING_MEDIUM
    ):

        contents = self.prepare_contents(messages)

        config = self.build_config(
            system_instruction,
            thinking_level
        )

        stream = self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config
        )

        for chunk in stream:

            text = chunk.text

            if text:
                yield text

    # =====================================================
    # PROVIDER NAME
    # =====================================================

    def get_provider_name(self):

        return "Google Gemini"
