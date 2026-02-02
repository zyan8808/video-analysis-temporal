from __future__ import annotations

from temporalio import activity

from app.constants import SUPPORTED_LANGUAGES


@activity.defn
async def extract_transcript(video: dict) -> dict:
    video_id = video.get("video_id", "unknown")
    transcript_text = (
        "This is a mock English transcript for video "
        f"{video_id}. It covers product updates and next steps."
    )
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
