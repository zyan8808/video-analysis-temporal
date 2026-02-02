import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.activities import extract_transcript, summarize_transcript, translate_transcript
from app.constants import TASK_QUEUE
from app.workflows import VideoProcessingWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[VideoProcessingWorkflow],
        activities=[extract_transcript, translate_transcript, summarize_transcript],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
