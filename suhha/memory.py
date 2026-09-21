"""Persistent memory for the agent: preferences, task history, and the
learned-rules file the agent rewrites over time. This file is what makes
the tool "evolve": its content is injected into every future system
prompt, so lessons learned in one session change behavior in the next.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import MEMORY_DIR

PREFERENCES_FILE = MEMORY_DIR / "preferences.json"
HISTORY_FILE = MEMORY_DIR / "history.jsonl"
RULES_FILE = MEMORY_DIR / "learned_rules.md"
FEEDBACK_FILE = MEMORY_DIR / "pending_feedback.jsonl"

DEFAULT_RULES = """# Learned rules

هنا القواعد اللي الوكيل اتعلمها من التجربة. بتتضاف تلقائي بعد كل جلسة
تعلّم (reflect). عدّليها يدويًا في أي وقت لو عايزة تصححي حاجة.
"""


def _ensure_dirs() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not RULES_FILE.exists():
        RULES_FILE.write_text(DEFAULT_RULES, encoding="utf-8")
    if not PREFERENCES_FILE.exists():
        PREFERENCES_FILE.write_text("{}", encoding="utf-8")


def load_preferences() -> dict:
    _ensure_dirs()
    return json.loads(PREFERENCES_FILE.read_text(encoding="utf-8") or "{}")


def save_preferences(prefs: dict) -> None:
    _ensure_dirs()
    PREFERENCES_FILE.write_text(
        json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_rules() -> str:
    _ensure_dirs()
    return RULES_FILE.read_text(encoding="utf-8")


def append_rules(new_section: str) -> None:
    """Append a new learned rule as its own dated section."""
    _ensure_dirs()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with RULES_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n## {stamp}\n{new_section.strip()}\n")


def log_task(task: str, result_summary: str, tool_calls: list[str]) -> None:
    _ensure_dirs()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "result_summary": result_summary,
        "tool_calls": tool_calls,
    }
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def record_feedback(text: str) -> None:
    """Explicit feedback from the user, consumed by the next reflect() run."""
    _ensure_dirs()
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "feedback": text}
    with FEEDBACK_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_recent_history(limit: int = 20) -> list[dict]:
    _ensure_dirs()
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:]]


def read_pending_feedback() -> list[dict]:
    _ensure_dirs()
    if not FEEDBACK_FILE.exists():
        return []
    lines = FEEDBACK_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def clear_pending_feedback() -> None:
    _ensure_dirs()
    FEEDBACK_FILE.write_text("", encoding="utf-8")
