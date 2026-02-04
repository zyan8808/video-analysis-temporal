"""
Optimized workflow that processes one video into multiple languages in parallel.
Shows the difference between sequential and parallel activity execution.
"""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

from app.activities import (
    extract_transcript,
    summarize_transcript,
    translate_summary,
    translate_transcript,
)


@workflow.defn
class VideoProcessingWorkflowSequential:
    """Original: Sequential processing (one language at a time)."""

    @workflow.run
    async def run(self, video: dict) -> dict:
        # Step 1: Extract transcript (English)
        transcript = await workflow.execute_activity(
            extract_transcript,
            video,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 2: Generate English summary, key takeaways, action items
        english_summary = await workflow.execute_activity(
            summarize_transcript,
            transcript,
            start_to_close_timeout=timedelta(seconds=25),
        )

        # Step 3 & 4: Translate transcript AND summary in parallel (independent tasks)
        target_language = video.get("target_language", "es")
        
        # Create both translation tasks
        translate_transcript_task = workflow.execute_activity(
            translate_transcript,
            args=(transcript, target_language),
            start_to_close_timeout=timedelta(seconds=20),
        )
        translate_summary_task = workflow.execute_activity(
            translate_summary,
            args=(english_summary, target_language),
            start_to_close_timeout=timedelta(seconds=20),
        )
        
        # Wait for both to complete (they run in parallel)
        translated_transcript = await translate_transcript_task
        translated_summary = await translate_summary_task

        return {
            "input": video,
            "transcript": transcript,
            "summary_en": english_summary,
            "translation": translated_transcript,
            "summary_translated": translated_summary,
        }


@workflow.defn
class VideoProcessingWorkflowParallel:
    """Optimized: Translate to multiple languages in parallel."""

    @workflow.run
    async def run(self, video: dict) -> dict:
        # Step 1: Extract transcript once (sequential - must be first)
        transcript = await workflow.execute_activity(
            extract_transcript,
            video,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 2: Translate to ALL target languages in parallel
        target_languages = video.get("target_languages", ["es"])

        # Create parallel translation tasks
        translation_tasks = [
            workflow.execute_activity(
                translate_transcript,
                args=(transcript, lang),
                start_to_close_timeout=timedelta(seconds=30),
            )
            for lang in target_languages
        ]

        # Wait for all translations to complete in parallel
        translations = await workflow.wait_for_all(*translation_tasks)

        # Step 3: Generate summaries in parallel for each translation
        summary_tasks = [
            workflow.execute_activity(
                summarize_transcript,
                translation,
                start_to_close_timeout=timedelta(seconds=30),
            )
            for translation in translations
        ]

        # Wait for all summaries to complete in parallel
        summaries = await workflow.wait_for_all(*summary_tasks)

        return {
            "input": video,
            "transcript": transcript,
            "translations": [
                {"language": t["language"], "translation": t, "summary": s}
                for t, s in zip(translations, summaries)
            ],
        }


@workflow.defn
class VideoProcessingWorkflowMixed:
    """
    Mixed approach: Sequential for dependencies, parallel for independent tasks.
    Example: Process video metadata extraction and transcript extraction in parallel.
    """

    @workflow.run
    async def run(self, video: dict) -> dict:
        # Parallel: Extract transcript AND fetch video metadata simultaneously
        # (if they don't depend on each other)
        transcript_task = workflow.execute_activity(
            extract_transcript,
            video,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Wait for parallel tasks
        transcript = await transcript_task

        # Sequential: Translation depends on transcript
        translation = await workflow.execute_activity(
            translate_transcript,
            args=(transcript, video.get("target_language", "es")),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Sequential: Summary depends on translation
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


# Default workflow used by worker/client examples
VideoProcessingWorkflow = VideoProcessingWorkflowSequential
