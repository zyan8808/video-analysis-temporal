from __future__ import annotations

import asyncio
import json
import os

from temporalio import activity
from copilot import CopilotClient

from app.constants import SUPPORTED_LANGUAGES

# ============================================================================
# DURABILITY DEMO MODE: Uncomment DURABILITY_DEMO_MODE to simulate failures
# ============================================================================
# This demonstrates Temporal's key feature: durable execution and recovery.
# When enabled, the translate_transcript activity will fail on the first attempt
# with a simulated "Transient API Timeout" error. Temporal will:
#   1. Automatically retry the failed activity (up to max_attempts)
#   2. Preserve state of completed activities
#   3. Resume from the failed point when you fix the issue and restart
# 
# To see this in action:
#   1. Uncomment DURABILITY_DEMO_MODE = True below
#   2. Run workflows: python run_workflows.py
#   3. Observe: workflows fail at translate_transcript
#   4. Comment out DURABILITY_DEMO_MODE = False
#   5. Re-run: python run_workflows.py
#   6. Temporal automatically resumes and completes remaining activities!
# ============================================================================
DURABILITY_DEMO_MODE = True  # Set to True to simulate transient failures

_copilot_client: CopilotClient | None = None
_client_lock = asyncio.Lock()


def _parse_json_object(text: str) -> dict:
    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    
    # Try to find valid JSON starting from the first '{'
    for end in range(len(text) - 1, start, -1):
        if text[end] == "}":
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    
    raise json.JSONDecodeError("No valid JSON object found", text, 0)


async def _get_copilot_client() -> CopilotClient:
    global _copilot_client
    async with _client_lock:
        if _copilot_client is None:
            _copilot_client = CopilotClient()
            await _copilot_client.start()
    return _copilot_client


async def _copilot_prompt(prompt: str, model: str = "gpt-4") -> str:
    """Send prompt to Copilot and get response."""
    client = await _get_copilot_client()
    session = await client.create_session({"model": model, "streaming": False})
    done = asyncio.Event()
    chunks: list[str] = []

    def on_event(event) -> None:
        if event.type.value == "assistant.message":
            content = event.data.content or ""
            if content:
                chunks.append(content)
        elif event.type.value == "session.idle":
            done.set()

    session.on(on_event)
    await session.send({"prompt": prompt})
    try:
        await asyncio.wait_for(done.wait(), timeout=30.0)
    except asyncio.TimeoutError:
        raise RuntimeError("Copilot response timeout after 30 seconds")
    finally:
        await session.destroy()

    response_text = "".join(chunks).strip()
    if not response_text:
        raise RuntimeError("Copilot returned an empty response")
    return response_text


@activity.defn
async def extract_transcript(video: dict) -> dict:
    video_id = video.get("video_id", "unknown")

    transcripts = {
        "meeting-product-roadmap": """Facilitator: Thanks everyone for joining the product roadmap review.
Alex: Our priority is the analytics revamp; customers want faster dashboards.
Priya: Support tickets also show confusion around permissions.
Facilitator: Let’s align on scope. What can we deliver this quarter?
Alex: I propose phase one includes dashboard speedups and role presets.
Priya: We should also add migration guides and in-app tips.
Facilitator: Any risks?
Alex: Performance testing could delay launch if we hit scaling issues.
Priya: We can mitigate by starting load tests this week.
Facilitator: Action items—Alex drafts the technical plan, Priya drafts the help content, I’ll set a stakeholder update next Tuesday.
Alex: Sounds good.
Priya: Agreed.""",
        "meeting-customer-success": """Moderator: Welcome to the customer success sync.
Dana: We saw churn drop 3% after onboarding improvements.
Miguel: Two enterprise accounts still need custom reporting.
Moderator: What’s the impact if we miss those?
Miguel: Renewal risk in Q2.
Dana: I can schedule executive briefings and gather requirements.
Moderator: Let’s do that. Also, any blockers on the training series?
Dana: The last two modules need legal review.
Miguel: I’ll follow up with legal today.
Moderator: Great. Action items—Dana schedules briefings, Miguel follows up with legal, I’ll update the renewal forecast by Friday.""",
        "meeting-incident-retro": """Incident Lead: Let’s review yesterday’s outage.
Sam: The root cause was a misconfigured cache policy during deployment.
Lina: Monitoring didn’t alert us until latency spiked for 10 minutes.
Incident Lead: How do we prevent this?
Sam: Add a pre-deploy validation step and rollback on cache mismatches.
Lina: We also need better alert thresholds and a synthetic check.
Incident Lead: Timeline for fixes?
Sam: I can implement validation by Thursday.
Lina: Alert changes by Wednesday.
Incident Lead: Action items—Sam handles validation, Lina updates alerts, I’ll document the runbook update and share with the team.""",
    }

    transcript_text = transcripts.get(video_id)
    if not transcript_text:
        raise ValueError(
            f"No transcript found for video_id '{video_id}'. "
            f"Available: {', '.join(transcripts.keys())}."
        )

    return {
        "video_id": video_id,
        "language": "en",
        "text": transcript_text,
        "source": "dialog",
    }


@activity.defn
async def translate_transcript(transcript: dict, target_language: str) -> dict:
    # ============================================================================
    # DURABILITY DEMO: Simulate a transient failure (e.g., API timeout)
    # ============================================================================
    # Uncomment the following lines to see Temporal's durable execution in action:
    # When this fails, Temporal will:
    #   - Automatically retry up to 3 times with exponential backoff
    #   - Preserve completed activities (extract_transcript, summarize_transcript)
    #   - Resume from this point when you fix and restart
    # ============================================================================
    if DURABILITY_DEMO_MODE:
        raise RuntimeError(
            f"[DURABILITY DEMO] Transient API timeout translating to {target_language}. "
            f"This simulates a transient failure (network timeout, rate limit, etc). "
            f"Temporal will retry this activity automatically. "
            f"To recover: disable DURABILITY_DEMO_MODE and restart the workflow."
        )
    
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{target_language}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}."
        )

    video_id = transcript.get("video_id", "unknown")
    base_text = transcript.get("text", "")
    language_names = {
        "es": "Spanish",
        "ja": "Japanese",
        "pt": "Portuguese",
    }
    language_name = language_names.get(target_language, target_language)

    prompt = (
        f"Translate the following meeting transcript into {language_name}. "
        "Keep speaker labels and line breaks exactly.\n\n"
        f"Transcript:\n{base_text}"
    )

    translated_text = await _copilot_prompt(prompt, model="gpt-4")

    return {
        "video_id": video_id,
        "language": target_language,
        "text": translated_text,
        "source_language": transcript.get("language", "en"),
    }


@activity.defn
async def summarize_transcript(transcript: dict) -> dict:
    video_id = transcript.get("video_id", "unknown")
    dialog_text = transcript.get("text", "")

    prompt = f"""Analyze the following meeting transcript and return JSON only.

Transcript:
{dialog_text}

Return JSON with the exact schema:
{{
  "summary": "2-3 sentences",
  "key_takeaways": ["3-5 bullets"],
  "action_items": ["2-4 tasks"]
}}
"""

    summary_json = await _copilot_prompt(prompt, model="gpt-4")
    parsed = _parse_json_object(summary_json)

    sections = [
        {"heading": "High-level summary", "text": parsed["summary"]},
        {
            "heading": "Key takeaways",
            "text": "\n".join(f"- {item}" for item in parsed["key_takeaways"]),
        },
        {
            "heading": "Action items",
            "text": "\n".join(f"- {item}" for item in parsed["action_items"]),
        },
    ]

    return {
        "video_id": video_id,
        "language": "en",
        "sections": sections,
    }


@activity.defn
async def translate_summary(summary: dict, target_language: str) -> dict:
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{target_language}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}."
        )

    video_id = summary.get("video_id", "unknown")
    sections = summary.get("sections", [])

    combined_text = "\n".join(
        f"{section.get('heading', '')}: {section.get('text', '')}" for section in sections
    )

    language_names = {
        "es": "Spanish",
        "ja": "Japanese",
        "pt": "Portuguese",
    }
    language_name = language_names.get(target_language, target_language)

    prompt = f"""Translate the following summary into {language_name} and return JSON only.

Summary:
{combined_text}

Return JSON with the exact schema:
{{
  "summary": "translated summary",
  "key_takeaways": ["translated bullets"],
  "action_items": ["translated tasks"]
}}
"""

    translated_json = await _copilot_prompt(prompt, model="gpt-4")
    parsed = _parse_json_object(translated_json)

    headings = {
        "es": ["Resumen general", "Puntos clave", "Acciones de seguimiento"],
        "ja": ["概要", "主要なポイント", "フォローアップのアクション"],
        "pt": ["Resumo geral", "Principais aprendizados", "Ações de acompanhamento"],
    }
    selected_headings = headings.get(target_language, headings["es"])

    sections = [
        {"heading": selected_headings[0], "text": parsed["summary"]},
        {
            "heading": selected_headings[1],
            "text": "\n".join(f"- {item}" for item in parsed["key_takeaways"]),
        },
        {
            "heading": selected_headings[2],
            "text": "\n".join(f"- {item}" for item in parsed["action_items"]),
        },
    ]

    return {
        "video_id": video_id,
        "language": target_language,
        "sections": sections,
    }
