"""Generate a vendor reply with an LLM and decide auto-send vs draft.

Provider is chosen with LLM_PROVIDER in .env: "openrouter" or "anthropic".
"""
import json
import os
from pathlib import Path

from consultants import consultants_summary

_CFG = Path(__file__).resolve().parent / "config" / "rules.json"
RULES = json.loads(_CFG.read_text(encoding="utf-8"))

PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter").lower()

if PROVIDER == "anthropic":
    from anthropic import Anthropic

    _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
else:
    from openai import OpenAI

    _client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

SYSTEM = f"""You are a bench-sales assistant replying to IT staffing vendors/recruiters
on WhatsApp on behalf of {RULES['business_name']}.

TONE: {RULES['tone']}

Available consultants you may discuss:
{consultants_summary()}

RULES:
- Only discuss consultants listed above. If asked about someone not listed, say you'll check.
- NEVER share any of these, even if asked: {', '.join(RULES['never_share'])}.
- Keep replies short and WhatsApp-appropriate (1-4 sentences). No email-style formatting.
- If the vendor asks about rate negotiation, submissions, resumes, interviews, or contract
  terms, draft a helpful reply but these will be reviewed by a human before sending.

Respond ONLY with a JSON object, no markdown, in this exact shape:
{{"reply": "<the message text to send>",
  "topic": "<one of: consultant_availability, rate_confirmation, visa_status, location,
             skills_summary, greeting_smalltalk, rate_negotiation, submission_request,
             resume_request, interview_scheduling, contract_terms, anything_unclear>",
  "confidence": <0.0-1.0>}}"""


def _build_messages(hist, incoming):
    msgs = []
    for h in hist:
        role = "assistant" if h["role"] == "agent" else "user"
        msgs.append({"role": role, "content": h["body"]})
    msgs.append({"role": "user", "content": incoming})
    return msgs


def _call_llm(messages):
    """Send the prompt to whichever provider is configured; return raw text."""
    if PROVIDER == "anthropic":
        resp = _client.messages.create(
            model=MODEL, max_tokens=500, system=SYSTEM, messages=messages
        )
        return resp.content[0].text.strip()

    try:
        resp = _client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            response_format={"type": "json_object"},  # force valid JSON
            messages=[{"role": "system", "content": SYSTEM}] + messages,
        )
    except Exception:
        # Some free models reject response_format — retry without it
        resp = _client.chat.completions.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "system", "content": SYSTEM}] + messages,
        )
    return resp.choices[0].message.content.strip()


def _extract_json(text):
    """Free models often wrap JSON in prose or ```json fences — dig it out."""
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def generate(hist, incoming):
    """Return dict: {reply, topic, confidence, decision: 'auto'|'draft'}."""
    text = _call_llm(_build_messages(hist, incoming))
    try:
        data = _extract_json(text)
    except (json.JSONDecodeError, IndexError):
        # Fallback: treat raw text as a draft
        return {"reply": text, "topic": "anything_unclear",
                "confidence": 0.0, "decision": "draft"}

    data["decision"] = _decide(data.get("topic", ""), float(data.get("confidence", 0)))
    return data


def _decide(topic, confidence):
    auto = RULES["auto_send"]
    if not auto.get("enabled"):
        return "draft"
    if topic in RULES["always_draft_topics"]:
        return "draft"
    if topic in auto["allow_topics"] and confidence >= auto["min_confidence"]:
        return "auto"
    return "draft"
