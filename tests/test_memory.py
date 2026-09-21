"""Sanity tests for memory.py. No network calls, no API key needed."""
from suhha import memory


def _patch_paths(monkeypatch, tmp_path):
    mem_dir = tmp_path / "memory"
    monkeypatch.setattr(memory, "MEMORY_DIR", mem_dir)
    monkeypatch.setattr(memory, "PREFERENCES_FILE", mem_dir / "preferences.json")
    monkeypatch.setattr(memory, "HISTORY_FILE", mem_dir / "history.jsonl")
    monkeypatch.setattr(memory, "RULES_FILE", mem_dir / "learned_rules.md")
    monkeypatch.setattr(memory, "FEEDBACK_FILE", mem_dir / "pending_feedback.jsonl")


def test_preferences_roundtrip(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    memory.save_preferences({"name": "Suha"})
    assert memory.load_preferences() == {"name": "Suha"}


def test_rules_default_then_append(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    assert "Learned rules" in memory.load_rules()
    memory.append_rules("- رد بإيجاز")
    assert "رد بإيجاز" in memory.load_rules()


def test_task_history_log_and_read(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    memory.log_task("مهمة تجريبية", "تم بنجاح", ["web_search"])
    history = memory.read_recent_history()
    assert len(history) == 1
    assert history[0]["task"] == "مهمة تجريبية"
    assert history[0]["tool_calls"] == ["web_search"]


def test_feedback_record_and_clear(tmp_path, monkeypatch):
    _patch_paths(monkeypatch, tmp_path)
    memory.record_feedback("الرد كان طويل")
    assert len(memory.read_pending_feedback()) == 1
    memory.clear_pending_feedback()
    assert memory.read_pending_feedback() == []
