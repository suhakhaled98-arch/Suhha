"""Central place for environment/config values."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT_DIR / "memory"

load_dotenv(ROOT_DIR / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_DEFAULT_REPO = os.environ.get("GITHUB_DEFAULT_REPO", "")

GOOGLE_CREDENTIALS_FILE = ROOT_DIR / "credentials.json"
GOOGLE_TOKEN_FILE = ROOT_DIR / "token.json"
