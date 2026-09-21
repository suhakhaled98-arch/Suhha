"""The core agent loop.

Every run injects the current learned_rules.md and preferences into the
system prompt, so anything the reflection step (suhha/learn.py) has added
in the past changes behavior in this run. That feedback loop -- act, log,
reflect, update rules, act again with new rules -- is the "self-evolving"
part of this tool.
"""
import json

import anthropic

from . import memory
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from .tools import github_tool, google_tool, web_search

BASE_PERSONA = """إنتِ Suhha، مساعد شخصي أوتوماتيكي. مهمتك تنفيذي المهام اللي
بتتطلبيها فعليًا باستخدام الأدوات المتاحة (إيميل، مواعيد، GitHub، بحث على
الإنترنت) بدل ما تجاوبي كلام نظري بس. لو أداة فشلت أو ناقصها إعدادات
(زي مفتاح API)، قولي بوضوح إيه المطلوب تظبيطه بدل ما تتخيلي نتيجة.
لو في تفضيلات محفوظة عن المستخدم، التزمي بيها من غير ما تسأليه تاني."""

TOOLS = [
    {
        "name": "web_search",
        "description": "ابحثي على الإنترنت عن معلومة أو خبر.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "هاتي نص صفحة ويب معينة عشان تلخصيها.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "github_list_issues",
        "description": "اعرضي الـ issues المفتوحة في ريبو GitHub.",
        "input_schema": {
            "type": "object",
            "properties": {"repo": {"type": "string", "description": "owner/repo, اختياري"}},
        },
    },
    {
        "name": "github_list_pull_requests",
        "description": "اعرضي الـ pull requests المفتوحة في ريبو GitHub.",
        "input_schema": {
            "type": "object",
            "properties": {"repo": {"type": "string", "description": "owner/repo, اختياري"}},
        },
    },
    {
        "name": "github_create_issue",
        "description": "افتحي issue جديد في ريبو GitHub.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "repo": {"type": "string"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "gmail_list_recent",
        "description": "اعرضي آخر الإيميلات.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "gmail_send",
        "description": "ابعتي إيميل.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "calendar_list_upcoming",
        "description": "اعرضي المواعيد الجاية في الكالندر.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "calendar_create_event",
        "description": "ضيفي ميعاد جديد في الكالندر.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "start_iso": {"type": "string", "description": "ISO 8601, e.g. 2026-01-01T10:00:00"},
                "end_iso": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    {
        "name": "save_preference",
        "description": "احفظي تفضيل دائم عن المستخدم عشان تتفتكر في المرات الجاية.",
        "input_schema": {
            "type": "object",
            "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            "required": ["key", "value"],
        },
    },
]


def _dispatch(name: str, tool_input: dict) -> str:
    try:
        if name == "web_search":
            return json.dumps(web_search.search(tool_input["query"]), ensure_ascii=False)
        if name == "fetch_page":
            return web_search.fetch_text(tool_input["url"])
        if name == "github_list_issues":
            return json.dumps(
                github_tool.list_open_issues(tool_input.get("repo")), ensure_ascii=False
            )
        if name == "github_list_pull_requests":
            return json.dumps(
                github_tool.list_open_pull_requests(tool_input.get("repo")), ensure_ascii=False
            )
        if name == "github_create_issue":
            return json.dumps(
                github_tool.create_issue(
                    tool_input["title"], tool_input.get("body", ""), tool_input.get("repo")
                ),
                ensure_ascii=False,
            )
        if name == "gmail_list_recent":
            return json.dumps(google_tool.list_recent_emails(), ensure_ascii=False)
        if name == "gmail_send":
            return json.dumps(
                google_tool.send_email(
                    tool_input["to"], tool_input["subject"], tool_input["body"]
                ),
                ensure_ascii=False,
            )
        if name == "calendar_list_upcoming":
            return json.dumps(google_tool.list_upcoming_events(), ensure_ascii=False)
        if name == "calendar_create_event":
            return json.dumps(
                google_tool.create_event(
                    tool_input["summary"],
                    tool_input["start_iso"],
                    tool_input["end_iso"],
                    tool_input.get("description", ""),
                ),
                ensure_ascii=False,
            )
        if name == "save_preference":
            prefs = memory.load_preferences()
            prefs[tool_input["key"]] = tool_input["value"]
            memory.save_preferences(prefs)
            return "saved"
        return f"unknown tool: {name}"
    except Exception as exc:  # tool failures go back to the model as text, not a crash
        return f"error: {exc}"


def _build_system_prompt() -> str:
    prefs = memory.load_preferences()
    rules = memory.load_rules()
    parts = [BASE_PERSONA]
    if prefs:
        parts.append("تفضيلات محفوظة عن المستخدم:\n" + json.dumps(prefs, ensure_ascii=False, indent=2))
    parts.append("قواعد اتعلمت من التجارب اللي فاتت:\n" + rules)
    return "\n\n".join(parts)


def run_task(task: str, max_turns: int = 8) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY مش متظبط في .env")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": task}]
    tool_calls_log = []

    for _ in range(max_turns):
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=_build_system_prompt(),
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(
                block.text for block in response.content if block.type == "text"
            )
            memory.log_task(task, final_text, tool_calls_log)
            return final_text

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            tool_calls_log.append(block.name)
            result = _dispatch(block.name, block.input)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            )
        messages.append({"role": "user", "content": tool_results})

    summary = "وصلت لحد أقصى عدد خطوات من غير ما أخلّص، جربي تقسمي المهمة."
    memory.log_task(task, summary, tool_calls_log)
    return summary
