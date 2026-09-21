"""The self-evolution step.

Reads recent task history + any explicit user feedback, asks Claude to
distill it into a short, concrete behavior rule, and appends that rule to
memory/learned_rules.md. Every future agent run loads that file into its
system prompt (see agent._build_system_prompt), so the lesson sticks.

This is deliberately NOT the agent rewriting its own source code -- that
would be unreviewable and unsafe to run unattended. Evolving a rules file
that a human can read, edit, or delete at any time is the honest version
of "learns over time".
"""
import anthropic

from . import memory
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL

REFLECT_PROMPT = """إنتِ بتحللي أداء وكيل شخصي عشان تحسّني قواعد سلوكه.

سجل آخر المهام اللي نفذها:
{history}

فيدباك صريح من المستخدم (لو موجود):
{feedback}

اطلعي بقاعدة سلوك واحدة أو اتنين بس، قصيرة وقابلة للتنفيذ، تضاف لملف
تعليمات الوكيل عشان يحسّن أداءه في المرات الجاية. لو مفيش حاجة تستاهل
تتضاف (الأداء كويس أو مفيش بيانات كفاية)، اكتبي بالظبط: NOTHING_TO_ADD.
ماتكتبيش مقدمات، طلعي القواعد نفسها بس كـ bullet points بالعربي المصري.
"""


def reflect(history_limit: int = 20) -> str:
    """Analyze recent history + pending feedback, update learned_rules.md.

    Returns the text that was appended, or a message explaining nothing
    changed.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY مش متظبط في .env")

    history = memory.read_recent_history(history_limit)
    feedback = memory.read_pending_feedback()

    if not history and not feedback:
        return "مفيش سجل مهام ولا فيدباك لسه، مفيش حاجة أتعلمها."

    history_text = "\n".join(
        f"- المهمة: {h['task']} | النتيجة: {h['result_summary'][:200]} | "
        f"أدوات استخدمها: {', '.join(h['tool_calls']) or 'مفيش'}"
        for h in history
    ) or "مفيش"
    feedback_text = "\n".join(f"- {f['feedback']}" for f in feedback) or "مفيش"

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": REFLECT_PROMPT.format(history=history_text, feedback=feedback_text),
            }
        ],
    )
    proposal = "".join(b.text for b in response.content if b.type == "text").strip()

    memory.clear_pending_feedback()

    if proposal == "NOTHING_TO_ADD" or not proposal:
        return "مفيش تعديل يستاهل يتضاف دلوقتي."

    memory.append_rules(proposal)
    return proposal
