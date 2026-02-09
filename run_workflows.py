"""
Example client demonstrating batch video processing with parallel execution.
Processes all videos in a single workflow for maximum efficiency.
"""

import asyncio
import json
from datetime import timedelta

from temporalio.client import Client

from app.constants import TASK_QUEUE
from app.workflows import VideoProcessingWorkflow


async def main() -> None:
    client = await Client.connect("localhost:7233")

    # Define multiple videos to process in a single batch
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

    print(f"Starting batch processing of {len(video_inputs)} videos...\n")

    # Execute the batch workflow with all videos
    # All extractions happen in parallel, then all summaries and translations happen in parallel
    workflow_id = f"batch-processing-{len(video_inputs)}-videos"
    try:
        handle = await client.start_workflow(
            VideoProcessingWorkflow.run,
            video_inputs,  # Pass entire list to batch workflow
            id=workflow_id,
            task_queue=TASK_QUEUE,
            execution_timeout=timedelta(minutes=5),
        )
    except Exception as e:
        if "already" in str(e).lower():
            # Workflow already running or completed
            handle = client.get_workflow_handle(workflow_id)
            print(f"Resuming existing workflow: {workflow_id}\n")
        else:
            raise

    # Wait for workflow to complete
    await asyncio.sleep(2)  # Give workflow a moment to start
    print(f"\n{'='*100}")
    print("PROCESSING RESULTS")
    print(f"{'='*100}\n")
    
    try:
        result = await handle.result()
        
        # Display results for all videos
        if "results" in result:
            for idx, video_result in enumerate(result["results"]):
                video_id = video_result.get("video_id", f"video-{idx}")
                
                print(f"✓ {video_id.upper()} - Completed Successfully\n")
                
                # Get target language from input
                target_lang = video_inputs[idx].get("target_language", "es")
                
                # Print transcript info
                transcript = video_result.get("transcript", {})
                print(f"📄 TRANSCRIPT:")
                print(f"  Language: {transcript.get('language', 'N/A')}")
                print(f"  Length: {len(transcript.get('text', ''))} characters\n")
                
                # Print summary
                summary = video_result.get("summary", {})
                if summary and "sections" in summary:
                    print(f"📝 ENGLISH SUMMARY:")
                    for section in summary.get("sections", []):
                        print(f"  {section.get('heading', '')}:")
                        print(f"    {section.get('text', '')}\n")
                
                # Print translated summary
                lang_names = {"es": "SPANISH", "ja": "JAPANESE", "pt": "PORTUGUESE"}
                translated_summary = video_result.get("translated_summary", {})
                if translated_summary and "sections" in translated_summary:
                    print(f"🌐 {lang_names.get(target_lang, target_lang.upper())} SUMMARY:")
                    for section in translated_summary.get("sections", []):
                        print(f"  {section.get('heading', '')}:")
                        print(f"    {section.get('text', '')}\n")
                
                print(f"{'─'*100}\n")
            
            print(f"✓ All {result.get('total_videos', len(video_inputs))} videos processed successfully!")
        else:
            print("Unexpected result format:")
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"✗ Workflow failed: {e}\n")
        desc = await handle.describe()
        print(f"Status: {desc.status.name}")
        if desc.status_message:
            print(f"Message: {desc.status_message}")

    print(f"{'='*100}\n")


if __name__ == "__main__":
    asyncio.run(main())
