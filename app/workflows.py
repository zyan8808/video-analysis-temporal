from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow

from app.activities import (
    extract_transcript,
    summarize_transcript,
    translate_summary,
    translate_transcript,
)


@workflow.defn
class VideoProcessingWorkflowBatch:
    """
    Batch processing: Process multiple videos in parallel.
    For each video:
      1. Extract transcript (sequential - must happen first)
      2. Summarize + Translate in parallel (independent tasks)
    All videos process simultaneously.
    """

    @workflow.run
    async def run(self, videos: list[dict]) -> dict:
        # Step 1: Extract transcripts for ALL videos in parallel
        extract_tasks = [
            workflow.execute_activity(
                extract_transcript,
                video,
                start_to_close_timeout=timedelta(seconds=30),
            )
            for video in videos
        ]
        
        # Wait for all extractions to complete
        transcripts = await asyncio.gather(*extract_tasks)

        # Step 2: For each transcript, run summarize + translate in parallel
        # This creates a task for every video
        all_summary_tasks = []
        all_translate_tasks = []
        
        for i, transcript in enumerate(transcripts):
            # Get target_language from the original video input (not from transcript)
            target_language = videos[i].get("target_language", "es")
            
            # Summarize this video
            summary_task = workflow.execute_activity(
                summarize_transcript,
                transcript,
                start_to_close_timeout=timedelta(seconds=25),
            )
            all_summary_tasks.append((transcript.get("video_id"), summary_task))
            
            # Translate this video
            translate_task = workflow.execute_activity(
                translate_transcript,
                args=(transcript, target_language),
                start_to_close_timeout=timedelta(seconds=20),
            )
            all_translate_tasks.append((transcript.get("video_id"), translate_task))
        
        # Wait for all summaries and translations to complete in parallel
        summaries = await asyncio.gather(*[task for _, task in all_summary_tasks])
        translations = await asyncio.gather(*[task for _, task in all_translate_tasks])

        # Step 3: Translate summaries in parallel
        all_translated_summary_tasks = []
        for i, transcript in enumerate(transcripts):
            # Get target_language from the original video input (not from transcript)
            target_language = videos[i].get("target_language", "es")
            
            # Translate the summary
            translated_summary_task = workflow.execute_activity(
                translate_summary,
                args=(summaries[i], target_language),
                start_to_close_timeout=timedelta(seconds=20),
            )
            all_translated_summary_tasks.append(translated_summary_task)
        
        # Wait for all translated summaries to complete
        translated_summaries = await asyncio.gather(*all_translated_summary_tasks)

        # Organize results by video
        results = []
        for i, transcript in enumerate(transcripts):
            results.append({
                "video_id": transcript.get("video_id"),
                "transcript": transcript,
                "summary": summaries[i],
                "translation": translations[i],
                "translated_summary": translated_summaries[i],
            })

        return {
            "total_videos": len(videos),
            "results": results,
        }


# Default workflow used by worker/client examples
VideoProcessingWorkflow = VideoProcessingWorkflowBatch
