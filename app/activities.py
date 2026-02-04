from __future__ import annotations

from temporalio import activity
from github_copilot_sdk import CopilotClient

from app.constants import SUPPORTED_LANGUAGES

# Initialize Copilot client (uses Copilot CLI authentication)
# Make sure you have installed and authenticated with: gh auth login
copilot_client = CopilotClient()


@activity.defn
async def extract_transcript(video: dict) -> dict:
    video_id = video.get("video_id", "unknown")
    
    # Enhanced dialog-based transcript with speaker interactions
    transcript_text = f"""Speaker 1: Welcome everyone to today's session on {video_id}!
Speaker 2: Thanks for having me. I'm excited to discuss our latest updates.
Speaker 1: Let's start with the product roadmap. What are the key highlights?
Speaker 2: We have three major features launching this quarter. First, we're introducing automated workflows.
Speaker 1: That sounds promising. How will this impact our current users?
Speaker 2: Great question. Users will see a 40% reduction in manual tasks, which means more time for strategic work.
Speaker 1: Excellent. What about the second feature?
Speaker 2: The second feature is enhanced analytics with real-time dashboards.
Speaker 1: I'm sure our customers will love that. And the third feature?
Speaker 2: The third is improved collaboration tools with integrated messaging and file sharing.
Speaker 1: Perfect. What are the next steps for our team?
Speaker 2: We need to schedule training sessions, update documentation, and gather feedback from early adopters.
Speaker 1: Great. Let's make sure we follow up with stakeholders and set clear timelines.
Speaker 2: Absolutely. I'll prepare a detailed action plan and share it with the team by end of week."""
    
    return {
        "video_id": video_id,
        "language": "en",
        "text": transcript_text,
        "source": "mock",
    }


@activity.defn
async def translate_transcript(transcript: dict, target_language: str) -> dict:
    if target_language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language '{target_language}'. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}."
        )

    video_id = transcript.get("video_id", "unknown")
    base_text = transcript.get("text", "")
    templates = {
        "es": "Transcripción traducida (ES) del video {video_id}: {text}",
        "ja": "ビデオ{video_id}の翻訳済み文字起こし（JA）: {text}",
        "pt": "Transcrição traduzida (PT) do vídeo {video_id}: {text}",
    }

    translated_text = templates[target_language].format(
        video_id=video_id,
        text=base_text,
    )

    return {
        "video_id": video_id,
        "language": target_language,
        "text": translated_text,
        "source_language": transcript.get("language", "en"),
    }


@activity.defn
async def summarize_transcript(translation: dict) -> dict:
    video_id = translation.get("video_id", "unknown")
    language = translation.get("language", "es")
    dialog_text = translation.get("text", "")

    # Prepare prompt for Copilot to generate structured summary
    prompt = f"""Analyze the following video transcript and provide a structured summary in {language} language.

Transcript:
{dialog_text}

Please provide the summary in the following format:
1. High-level summary (2-3 sentences)
2. Key takeaways (3-5 bullet points)
3. Action items (2-4 specific follow-up tasks)

Ensure all text is in {language} language."""

    try:
        # Use Copilot SDK to generate AI-powered summary
        response = await copilot_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes video transcripts."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4",
            temperature=0.7,
        )
        
        summary_text = response.choices[0].message.content
        
        # Parse the AI-generated summary into structured format
        # For now, return it as a single structured response
        # You can enhance this to parse the response into separate sections
        
        headings = {
            "es": ["Resumen general", "Puntos clave", "Acciones de seguimiento"],
            "ja": ["概要", "主要なポイント", "フォローアップのアクション"],
            "pt": ["Resumo geral", "Principais aprendizados", "Ações de acompanhamento"],
        }
        
        selected_headings = headings.get(language, headings["es"])
        
        # Simple parsing - in production, you'd want more sophisticated parsing
        sections = [
            {"heading": selected_headings[0], "text": f"AI-generated summary for {video_id}"},
            {"heading": selected_headings[1], "text": summary_text[:200]},
            {"heading": selected_headings[2], "text": "Follow-up actions based on AI analysis"},
        ]
        
    except Exception as e:
        # Fallback to mock data if Copilot API fails
        headings = {
            "es": ["Resumen general", "Puntos clave", "Acciones de seguimiento"],
            "ja": ["概要", "主要なポイント", "フォローアップのアクション"],
            "pt": ["Resumo geral", "Principais aprendizados", "Ações de acompanhamento"],
        }
        
        summary_templates = {
            "es": [
                f"El video {video_id} presenta actualizaciones del producto y próximos pasos.",
                "Se destacó el progreso reciente y la alineación del equipo.",
                "Programar una revisión y compartir notas con las partes interesadas.",
            ],
            "ja": [
                f"ビデオ{video_id}では製品更新と次のステップが説明されています。",
                "最近の進捗とチームの整合性が強調されました。",
                "レビューを予定し、関係者にメモを共有します。",
            ],
            "pt": [
                f"O vídeo {video_id} apresenta atualizações do produto e próximos passos.",
                "Foram destacados o progresso recente e o alinhamento da equipe.",
                "Agendar uma revisão e compartilhar notas com as partes interessadas.",
            ],
        }
        
        selected_headings = headings.get(language, headings["es"])
        selected_templates = summary_templates.get(language, summary_templates["es"])
        
        sections = [
            {"heading": heading, "text": text}
            for heading, text in zip(selected_headings, selected_templates)
        ]

    return {
        "video_id": video_id,
        "language": language,
        "sections": sections,
    }
