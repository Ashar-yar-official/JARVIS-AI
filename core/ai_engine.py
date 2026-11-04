
from abc import ABC, abstractmethod
from typing import Optional, Callable, Iterator


# =========================================================
# AI ENGINE CONFIGURATION
# =========================================================

DEFAULT_SYSTEM_INSTRUCTION = """
You are JARVIS (Just A Rather Very Intelligent System),
a professional desktop AI assistant.

Your personality:
- Professional British male assistant style.
- Calm, intelligent, clear and articulate.
- Helpful, respectful and concise.

Your responsibilities:
- Understand the user's natural-language requests.
- Answer questions and explain technical topics.
- Help plan tasks and suggest solutions.
- Clearly explain proposed computer operations.

Important safety rules:
- Never claim that you have performed an operation
  unless the local application confirms it.
- Never assume you have direct access to the user's computer.
- Never generate instructions that bypass JARVIS security controls.
- Treat computer operations as proposals requiring
  validation by JARVIS's local safety system.
- Never request or expose passwords, API keys or other secrets.
"""


# =========================================================
# THINKING LEVELS
# =========================================================

THINKING_LOW = "LOW"
THINKING_MEDIUM = "MEDIUM"
THINKING_HIGH = "HIGH"


# =========================================================
# AI ENGINE ERRORS
# =========================================================

class AIEngineError(Exception):
    pass


class ProviderNotConfiguredError(AIEngineError):
    pass


class InvalidAIResponseError(AIEngineError):
    pass


class AIProviderConnectionError(AIEngineError):
    pass


# =========================================================
# AI PROVIDER INTERFACE
# =========================================================

class AIProvider(ABC):

    @abstractmethod
    def generate_response(
        self,
        messages: list,
        system_instruction: str,
        thinking_level: str = THINKING_MEDIUM
    ) -> str:
        pass

    def generate_response_stream(
        self,
        messages: list,
        system_instruction: str,
        thinking_level: str = THINKING_MEDIUM
    ) -> Iterator[str]:

        # Default compatibility implementation.
        # Providers can override this to stream actual chunks.

        response = self.generate_response(
            messages,
            system_instruction,
            thinking_level
        )

        if response:
            yield response

    def get_provider_name(self) -> str:
        return self.__class__.__name__


# =========================================================
# MAIN AI ENGINE
# =========================================================

class AIEngine:

    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION
    ):

        self.provider = provider
        self.system_instruction = system_instruction

        self.conversation_history = []

        self.enabled = provider is not None

        self.last_thinking_level = None

    # =====================================================
    # CONFIGURE PROVIDER
    # =====================================================

    def set_provider(self, provider: AIProvider):

        if not isinstance(provider, AIProvider):
            raise TypeError(
                "Provider must inherit from AIProvider."
            )

        self.provider = provider
        self.enabled = True

    # =====================================================
    # DISCONNECT PROVIDER
    # =====================================================

    def disconnect_provider(self):

        self.provider = None
        self.enabled = False

    # =====================================================
    # CHECK CONNECTION STATUS
    # =====================================================

    def is_configured(self):

        return self.provider is not None and self.enabled

    # =====================================================
    # GET ENGINE STATUS
    # =====================================================

    def get_status(self):

        if not self.enabled:
            status = "DISABLED"

        elif self.provider is None:
            status = "NOT CONFIGURED"

        else:
            status = "READY"

        return {
            "enabled": self.enabled,
            "configured": self.provider is not None,
            "status": status,
            "provider": (
                self.provider.get_provider_name()
                if self.provider is not None
                else None
            ),
            "session_messages": len(
                self.conversation_history
            ),
            "last_thinking_level": self.last_thinking_level
        }

    # =====================================================
    # VALIDATE USER MESSAGE
    # =====================================================

    @staticmethod
    def validate_message(message):

        if not isinstance(message, str):
            raise TypeError(
                "Message must be a string."
            )

        message = message.strip()

        if not message:
            raise ValueError(
                "Message cannot be empty."
            )

        return message

    # =====================================================
    # AUTOMATIC THINKING LEVEL SELECTION
    # =====================================================

    @staticmethod
    def select_thinking_level(message):

        text = message.lower().strip()

        words = text.split()

        simple_phrases = {
            "hi",
            "hello",
            "hey",
            "hello jarvis",
            "hi jarvis",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
            "thank you",
            "thanks",
            "goodbye",
            "bye",
            "who are you",
            "introduce yourself"
        }

        if text in simple_phrases or len(words) <= 3:
            return THINKING_LOW

        high_keywords = (
            "debug",
            "debugging",
            "troubleshoot",
            "troubleshooting",
            "architecture",
            "algorithm",
            "optimise",
            "optimize",
            "analyse",
            "analyze",
            "comprehensive",
            "step by step",
            "multi-step",
            "compare and evaluate",
            "security vulnerability",
            "system design",
            "refactor",
            "write a program",
            "write code",
            "generate code",
            "explain this code",
            "find the bug",
            "fix this code",
            "complex"
        )

        if any(keyword in text for keyword in high_keywords):
            return THINKING_HIGH

        if len(words) >= 70 or len(message) >= 450:
            return THINKING_HIGH

        medium_keywords = (
            "explain",
            "describe",
            "how does",
            "how do",
            "why does",
            "why do",
            "recommend",
            "suggest",
            "plan",
            "calculate",
            "difference between",
            "advantages",
            "disadvantages",
            "summarise",
            "summarize",
            "solve"
        )

        if any(keyword in text for keyword in medium_keywords):
            return THINKING_MEDIUM

        return THINKING_MEDIUM

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(self, message):

        return self.send_message_stream(message)

    # =====================================================
    # SEND MESSAGE WITH STREAMING SUPPORT
    # =====================================================

    def send_message_stream(
        self,
        message,
        on_chunk: Optional[Callable[[str], None]] = None
    ):

        message = self.validate_message(message)

        if not self.enabled or self.provider is None:
            raise ProviderNotConfiguredError(
                "No AI provider is currently configured."
            )

        thinking_level = self.select_thinking_level(
            message
        )

        request_messages = (
            self.conversation_history.copy()
        )

        request_messages.append({
            "role": "user",
            "content": message
        })

        response_parts = []

        try:

            chunks = self.provider.generate_response_stream(
                request_messages,
                self.system_instruction,
                thinking_level
            )

            for chunk in chunks:

                if not isinstance(chunk, str):
                    raise InvalidAIResponseError(
                        "The AI provider returned a non-text chunk."
                    )

                if not chunk:
                    continue

                response_parts.append(chunk)

                if on_chunk is not None:
                    on_chunk(chunk)

        except AIEngineError:
            raise

        except Exception as error:

            raise AIProviderConnectionError(
                f"Unable to communicate with AI provider: {error}"
            ) from error

        response = "".join(response_parts).strip()

        if not response:
            raise InvalidAIResponseError(
                "The AI provider returned an empty response."
            )

        # Save conversation only after successful completion.

        self.conversation_history.append({
            "role": "user",
            "content": message
        })

        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })

        self.last_thinking_level = thinking_level

        return response

    # =====================================================
    # GET SESSION HISTORY
    # =====================================================

    def get_conversation_history(self):

        return self.conversation_history.copy()

    # =====================================================
    # RESET SESSION
    # =====================================================

    def reset_session(self):

        self.conversation_history.clear()
        self.last_thinking_level = None

    # Compatibility with ChatDialog
    def reset_conversation(self):

        self.reset_session()

    # =====================================================
    # UPDATE SYSTEM INSTRUCTION
    # =====================================================

    def set_system_instruction(self, instruction):

        if not isinstance(instruction, str):
            raise TypeError(
                "System instruction must be a string."
            )

        instruction = instruction.strip()

        if not instruction:
            raise ValueError(
                "System instruction cannot be empty."
            )

        self.system_instruction = instruction
