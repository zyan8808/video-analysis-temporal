"""
Example client demonstrating parallel video processing with varied content.
Customize video_inputs list to process different videos concurrently.
"""

import asyncio
import json
from datetime import timedelta

from temporalio.client import Client

from app.constants import TASK_QUEUE
from app.workflows import VideoProcessingWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    # Define multiple videos to process in parallel
    # Customize this list with your own video IDs and target languages
    video_inputs = [
        {
            "video_id": "meeting-product-roadmap",
            "source_language": "en",
            "target_language": "es",
            "description": "Product roadmap planning session",
        },
        {
            "video_id": "meeting-customer-success",
            "source_language": "en",
            "target_language": "ja",
            "description": "Customer success weekly sync",
        },
        {
            "video_id": "meeting-incident-retro",
            "source_language": "en",
            "target_language": "pt",
            "description": "Incident retrospective",
        },
    ]

    print(f"Starting parallel processing of {len(video_inputs)} videos...\n")

    # Create workflow tasks
    tasks = []
    for video in video_inputs:
        task = client.execute_workflow(
            VideoProcessingWorkflow.run,
            video,
            id=(
                f"video-{video['video_id']}-"
                f"{video['target_language']}-"
                f"{asyncio.get_event_loop().time()}"
            ),
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(minutes=2),
        )
        tasks.append(task)

    # Execute all workflows in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Display results
    print(f"\n{'='*100}")
    print("PROCESSING COMPLETE")
    print(f"{'='*100}\n")

    for video_input, result in zip(video_inputs, results):
        print(f"\n{'─'*100}")
        print(f"📹 Video ID: {video_input['video_id']}")
        print(f"🌐 Target Language: {video_input['target_language']}")
        print(f"📝 Description: {video_input.get('description', 'N/A')}")
        print(f"{'─'*100}")

        if isinstance(result, Exception):
            print(f"❌ ERROR: {result}")
        else:
            summary_en = result.get("summary_en", {})
            summary_translated = result.get("summary_translated", {})

            print("\n📊 SUMMARY (EN):")
            for section in summary_en.get("sections", []):
                print(f"  • {section['heading']}: {section['text']}")

            print(
                f"\n📊 SUMMARY ({summary_translated.get('language', 'unknown').upper()}):"
            )
            for section in summary_translated.get("sections", []):
                print(f"  • {section['heading']}: {section['text']}")

    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    asyncio.run(main())
