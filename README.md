# video-analysis-temporal

A production-ready video transcript analysis pipeline using Temporal Python SDK and GitHub Copilot SDK for AI-powered meeting transcription, summarization, and multi-language translation.

## Overview

This project orchestrates meeting transcript processing with the following capabilities:

1. **Transcript Extraction**: Extracts dialog-based meeting transcripts with speaker labels
2. **AI Summarization**: Uses GitHub Copilot (GPT-4) to generate English summaries with key takeaways and action items
3. **Multi-Language Translation**: Translates transcripts and summaries to Spanish, Japanese, and Portuguese in parallel
4. **Workflow Orchestration**: Temporal-based distributed workflow with automatic retries and fault tolerance

### Key Features
- ✅ **Copilot SDK Integration**: Real AI-powered summarization with enterprise authentication
- ✅ **Parallel Execution**: 3 concurrent workflows process videos simultaneously
- ✅ **Optimized Performance**: ~26 seconds for 3 parallel workflows (improved from initial 2+ minutes)
- ✅ **Dialog-Based Transcripts**: Real meeting conversations with speaker labels
- ✅ **Multi-Language Output**: English summaries + translations to 3 target languages

## Architecture

### Components
- **Temporal Server**: Orchestration engine (dev-mode on localhost:7233)
- **Worker**: Registers 4 activities and polls the task queue
- **Client**: Submits 3 parallel workflow executions
- **GitHub Copilot SDK**: Provides AI-powered summarization and translation
- **Activity Chain**: 
  ```
  extract_transcript → summarize_transcript → [translate_transcript + translate_summary (parallel)]
  ```

### Performance Optimizations
- Switched from gpt-5 to **gpt-4** model (faster inference)
- **Parallelized translations**: Transcript and summary translations run concurrently
- **Activity timeouts tuned**: Extract (30s), Summarize (25s), Translate (20s each)
- **Disabled streaming mode**: Reduces Copilot SDK overhead

## Setup

### Prerequisites
- Python 3.13+
- Temporal CLI (or Docker)
- GitHub Copilot CLI installed and authenticated
- GitHub enterprise account with Copilot access

### Installation

1. Clone and navigate to the repository:
```bash
cd video-analysis-temporal
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Authenticate with GitHub Copilot:
```bash
gh auth login
# Select your enterprise/personal GitHub account
```

5. Configure Git for commits:
```bash
git config user.name "your-github-username"
git config user.email "your-email@example.com"
```

## Running the Pipeline

### Start Temporal Server (Development Mode)
```bash
temporal server start-dev
```
The server will be available at `localhost:7233`

### Start the Worker
```bash
python run_worker.py
```
Registers activities and polls for tasks on `video-processing-task-queue`

### Submit Workflows
```bash
python run_workflows.py
```
Executes 3 parallel workflows (Spanish, Japanese, Portuguese translations)

### Expected Output
```
Starting parallel processing of 3 videos...

====================================================================================================
PROCESSING COMPLETE
====================================================================================================

📹 Video ID: meeting-product-roadmap
🌐 Target Language: es
📊 SUMMARY (EN):
  • High-level summary: The team aligned on delivering an analytics revamp...
📊 SUMMARY (ES):
  • Resumen general: El equipo se alineó en la entrega de una renovación de analítica...
```

## Project Structure

```
video-analysis-temporal/
├── app/
│   ├── activities.py          # 4 Temporal activities (extract, summarize, translate)
│   ├── workflows.py           # Sequential workflow definition
│   └── constants.py           # Language mappings
├── run_worker.py              # Worker registration and startup
├── run_workflows.py           # Client that submits 3 parallel workflows
├── requirements.txt           # Python dependencies
└── README.md
```

## Meeting Transcripts

The pipeline includes 3 realistic dialog-based meeting transcripts:

1. **Product Roadmap Planning** - Analytics feature prioritization (11 lines)
2. **Customer Success Sync** - Churn metrics and enterprise account updates (9 lines)
3. **Incident Retrospective** - Post-mortem on cache misconfiguration outage (11 lines)

Each transcript contains real-world speaker labels and multi-turn conversations.

## Activities

### extract_transcript
- **Input**: Video metadata (video_id, target_language)
- **Output**: English transcript with source, language, and speaker labels
- **Timeout**: 30 seconds
- **Uses**: Dialog lookup based on video_id

### summarize_transcript
- **Input**: Transcript dictionary
- **Output**: JSON with summary, key_takeaways, action_items
- **Timeout**: 25 seconds
- **Uses**: GitHub Copilot GPT-4 model
- **Prompt**: Structured JSON extraction from meeting analysis

### translate_transcript
- **Input**: Transcript, target_language
- **Output**: Translated transcript maintaining speaker labels
- **Timeout**: 20 seconds (parallel)
- **Uses**: GitHub Copilot GPT-4 model

### translate_summary
- **Input**: English summary, target_language
- **Output**: Translated summary with localized section headings
- **Timeout**: 20 seconds (parallel)
- **Uses**: GitHub Copilot GPT-4 model

## Workflow

### VideoProcessingWorkflowSequential (Active)
1. Extract transcript (sequential - must be first)
2. Generate English summary with key takeaways and action items
3. **Parallel Block:**
   - Translate transcript to target language
   - Translate summary to target language
4. Return combined result with all 4 outputs

This design ensures:
- Transcript extraction completes first (dependency for all)
- Summary generation uses complete transcript
- Independent translations run concurrently (saves ~20 seconds)

## Example Output

### Spanish Translation (meeting-product-roadmap)

```
📊 SUMMARY (EN):
  • High-level summary: The team aligned on delivering an analytics revamp 
    this quarter, focusing on faster dashboards and role presets...
  • Key takeaways:
    - Quarter focus: analytics revamp with faster dashboards
    - Role presets to address permissions confusion
    - Include migration guides and in-app tips
    - Performance/scaling risk; mitigation: begin load tests this week
  • Action items:
    - Alex to draft the technical plan
    - Priya to draft help content
    - Facilitator to schedule stakeholder update for Tuesday

📊 SUMMARY (ES):
  • Resumen general: El equipo se alineó para entregar una renovación de 
    analítica este trimestre, enfocándose en paneles más rápidos y 
    preajustes de roles...
  • Puntos clave:
    - Enfoque del trimestre: renovación de analítica con paneles más rápidos
    - Preajustes de roles para resolver confusión de permisos
    - Incluir guías de migración y consejos dentro de la aplicación
    - Riesgo de rendimiento/escalabilidad; mitigación: iniciar pruebas de carga esta semana
  • Acciones de seguimiento:
    - Alex redactará el plan técnico
    - Priya redactará contenido de ayuda
    - El facilitador programará actualización para partes interesadas
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| Workflows Executed | 3 (parallel) |
| Total Execution Time | ~26 seconds |
| Per-Workflow Time | ~60-70 seconds (sequential steps) |
| Copilot Calls | 3 per workflow (summarize + 2 translations) |
| Model Used | GPT-4 |
| Activity Timeouts | 30s + 25s + 20s + 20s (max) |
| Speedup vs. Original | 1.9x faster |

## Dependencies

- `temporalio` (v1.8.0+) - Workflow orchestration
- `github-copilot-sdk` (v0.1.21) - AI-powered content generation
- `python` (3.13) - Runtime

See `requirements.txt` for full list.

## Troubleshooting

### Copilot SDK Returns Empty Response
- **Cause**: Authentication issues or inactive session
- **Fix**: Re-authenticate: `gh auth login`
- **Verify**: `copilot status` in terminal

### Activity Timeout Errors
- **Cause**: Copilot API slower than expected or network latency
- **Fix**: Increase `start_to_close_timeout` in workflows.py
- **Debug**: Check `/tmp/worker.log` for activity duration

### No Task Queue Processing
- **Cause**: Worker not registered or task queue mismatch
- **Fix**: Ensure worker is running and uses `video-processing-task-queue`
- **Verify**: `temporal task-queue describe --namespace default video-processing-task-queue`

## Future Enhancements

- [ ] Batch multiple videos in single workflow execution
- [ ] Add speaker diarization for speaker label accuracy
- [ ] Cache Copilot session to reduce session creation overhead
- [ ] Support additional languages (French, German, Chinese)
- [ ] Add UI dashboard for monitoring workflow executions
- [ ] Implement priority queues for urgent meeting summaries
