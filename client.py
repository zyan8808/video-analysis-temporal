import asyncio
import json
from datetime import timedelta

from temporalio.client import Client

from app.constants import TASK_QUEUE, SUPPORTED_LANGUAGES
from app.workflows import VideoProcessingWorkflow


async def process_video(client: Client, video_input: dict) -> dict:
    """Process a single video workflow."""
    result = await client.execute_workflow(
        VideoProcessingWorkflow.run,
        video_input,
        id=f"video-processing-{video_input['video_id']}-{video_input['target_language']}",
        task_queue=TASK_QUEUE,
        execution_timeout=timedelta(minutes=1),
    )
    return result


async def main() -> None:
    client = await Client.connect("localhost:7233")

    # Create multiple video inputs with various content
    video_inputs = [
        {"video_id": "demo-001", "source_language": "en", "target_language": "es"},
        {"video_id": "demo-001", "source_language": "en", "target_language": "ja"},
        {"video_id": "demo-001", "source_language": "en", "target_language": "pt"},
        {"video_id": "product-launch-2024", "source_language": "en", "target_language": "es"},
        {"video_id": "product-launch-2024", "source_language": "en", "target_language": "ja"},
        {"video_id": "team-meeting-q1", "source_language": "en", "target_language": "es"},
        {"video_id": "team-meeting-q1", "source_language": "en", "target_language": "pt"},
        {"video_id": "training-session-101", "source_language": "en", "target_language": "ja"},
    ]

    # Process all videos in parallel
    print(f"Processing {len(video_inputs)} videos in parallel...\n")
    
    tasks = [process_video(client, video_input) for video_input in video_inputs]
    results = await asyncio.gather(*tasks)

    # Display results
    for video_input, result in zip(video_inputs, results):
        print(f"\n{'='*80}")
        print(f"Video: {video_input['video_id']} | Language: {video_input['target_language']}")
        print(f"{'='*80}")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
