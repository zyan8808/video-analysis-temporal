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
        # Use start_workflow() to return immediately without blocking
        # Workflows run in the background and results are fetched later
        workflow_id = (
            f"video-{video['video_id']}-"
            f"{video['target_language']}-durability-demo"
        )
        try:
            task = client.start_workflow(
                VideoProcessingWorkflow.run,
                video,
                id=workflow_id,
                task_queue=TASK_QUEUE,
                execution_timeout=timedelta(minutes=2),
            )
            tasks.append((workflow_id, task, "new"))
        except Exception as e:
            if "already" in str(e).lower():
                # Workflow already running or completed - get its handle to check status
                workflow_handle = client.get_workflow_handle(workflow_id)
                tasks.append((workflow_id, workflow_handle, "existing"))
            else:
                raise

    workflow_ids = []
    for entry in tasks:
        workflow_id = entry[0]
        task_or_handle = entry[1]
        status = entry[2]
        
        if status == "new":
            run_id = await task_or_handle
            workflow_ids.append(workflow_id)
            _ = run_id
        else:
            workflow_ids.append(workflow_id)

    # Wait for all workflows to complete and display results
    await asyncio.sleep(2)  # Give workflows a moment to start
    print(f"\n{'='*100}")
    print("PROCESSING RESULTS")
    print(f"{'='*100}\n")
    
    for idx, workflow_id in enumerate(workflow_ids):
        handle = client.get_workflow_handle(workflow_id)
        video = video_inputs[idx]
        video_id = video["video_id"]
        target_language = video["target_language"]
        
        try:
            result = await handle.result()
            # Workflow completed successfully
            print(f"✓ {video_id.upper()} - Completed Successfully\n")
            
            if "english_summary" in result and "translated_summary" in result:
                # Print English summary
                print(f"📝 ENGLISH SUMMARY:")
                eng_summary = result["english_summary"]
                for section in eng_summary.get("sections", []):
                    print(f"  {section.get('heading', '')}:")
                    print(f"    {section.get('text', '')}\n")
                
                # Print translated summary
                lang_names = {"es": "SPANISH", "ja": "JAPANESE", "pt": "PORTUGUESE"}
                print(f"🌐 {lang_names.get(target_language, target_language.upper())} SUMMARY:")
                trans_summary = result["translated_summary"]
                for section in trans_summary.get("sections", []):
                    print(f"  {section.get('heading', '')}:")
                    print(f"    {section.get('text', '')}\n")
        except Exception as e:
            # Workflow failed - try to get partial results from state
            desc = await handle.describe()
            if desc.status.name == "FAILED":
                print(f"⚠ {video_id.upper()} - Failed at Translation (Activities Completed)\n")
                
                # Try to extract English summary from workflow state
                try:
                    state = await handle.query("get_english_summary")
                    if state:
                        print(f"📝 ENGLISH SUMMARY (Before Failed Translation):")
                        for section in state.get("sections", []):
                            print(f"  {section.get('heading', '')}:")
                            print(f"    {section.get('text', '')}\n")
                except:
                    # If query not available, just note the failure
                    print(f"  English summary is available on the dashboard.\n")
            else:
                print(f"✗ {video_id.upper()} - {desc.status.name}\n")
        
        print(f"{'─'*100}\n")

    print(f"{'='*100}\n")

if __name__ == "__main__":
    asyncio.run(main())
