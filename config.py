# config.py
import os

DEFAULT_TITLE = "marcy's ChatBot"
USER_NAME = "user"
ASSISTANT_NAME = "assistant"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PROVIDER = "Anthropic"
MODEL = "claude-3-haiku-20240307"
MAX_TOKENS = 2048
SYSTEM = "必ず日本語で返答してください。"