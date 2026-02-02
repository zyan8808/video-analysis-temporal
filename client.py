import asyncio
import json
from datetime import timedelta

from temporalio.client import Client

from app.constants import TASK_QUEUE, SUPPORTED_LANGUAGES
from app.workflows import VideoProcessingWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    for target_language in SUPPORTED_LANGUAGES:
        video_input = {
            "video_id": "demo-001",
            "source_language": "en",
            "target_language": target_language,
        }

        result = await client.execute_workflow(
            VideoProcessingWorkflow.run,
            video_input,
            id=f"video-processing-{video_input['video_id']}-{target_language}",
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(minutes=1),
        )

        print(f"\nResult for language: {target_language}")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
