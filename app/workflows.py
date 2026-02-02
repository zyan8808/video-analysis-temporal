from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

from app.activities import extract_transcript, summarize_transcript, translate_transcript


@workflow.defn
class VideoProcessingWorkflow:
    @workflow.run
    async def run(self, video: dict) -> dict:
        transcript = await workflow.execute_activity(
            extract_transcript,
            video,
            start_to_close_timeout=timedelta(seconds=30),
        )

        translation = await workflow.execute_activity(
            translate_transcript,
            args=(transcript, video.get("target_language", "es")),
            start_to_close_timeout=timedelta(seconds=30),
        )

        summary = await workflow.execute_activity(
            summarize_transcript,
            translation,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "input": video,
            "transcript": transcript,
            "translation": translation,
            "summary": summary,
        }
