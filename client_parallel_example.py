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
            "video_id": "webinar-2024-q1",
            "source_language": "en",
            "target_language": "es",
            "description": "Q1 webinar about new features",
        },
        {
            "video_id": "webinar-2024-q1",
            "source_language": "en",
            "target_language": "ja",
            "description": "Q1 webinar about new features",
        },
        {
            "video_id": "customer-success-story",
            "source_language": "en",
            "target_language": "pt",
            "description": "Customer testimonial video",
        },
        {
            "video_id": "onboarding-101",
            "source_language": "en",
            "target_language": "es",
            "description": "Employee onboarding session",
        },
        {
            "video_id": "quarterly-review",
            "source_language": "en",
            "target_language": "ja",
            "description": "Quarterly business review",
        },
    ]

    print(f"Starting parallel processing of {len(video_inputs)} videos...\n")

    # Create workflow tasks
    tasks = []
    for video in video_inputs:
        task = client.execute_workflow(
            VideoProcessingWorkflow.run,
            video,
            id=f"video-{video['video_id']}-{video['target_language']}-{asyncio.get_event_loop().time()}",
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
            # Print summary section only for brevity
            summary = result.get("summary", {})
            print(f"\n📊 SUMMARY ({summary.get('language', 'unknown').upper()}):")
            for section in summary.get("sections", []):
                print(f"  • {section['heading']}: {section['text']}")

    print(f"\n{'='*100}\n")


if __name__ == "__main__":
    asyncio.run(main())
