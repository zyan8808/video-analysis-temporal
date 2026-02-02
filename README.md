# video-analysis-temporal
Testing project using Temporal Python SDK to simulate a video transcript pipeline.

## Overview
This pipeline simulates:
1. Extracting an English transcript from a video (mocked).
2. Translating the transcript into a fixed set of languages (Spanish, Japanese, Portuguese).
3. Generating a localized summary with translated section headings.

The workflow returns a nested dict per stage (`input`, `transcript`, `translation`, `summary`).

## Workflow stages
- `extract_transcript` (mock): produces a deterministic English transcript.
- `translate_transcript` (sync): produces a deterministic translation per target language.
- `summarize_transcript` (async): returns three sections: high-level summary, key takeaways, follow-up action items.

## Fixed task queue
`video-processing-task-queue`

## Setup
1. Start a Temporal server locally (for example, via Temporal CLI or Docker).
2. Install dependencies:

```
pip install -r requirements.txt
```

## Run the worker
```
python worker.py
```

## Run the client
```
python client.py
```

## Example outputs

### Spanish (`es`)
```
{
	"input": {
		"video_id": "demo-001",
		"source_language": "en",
		"target_language": "es"
	},
	"transcript": {
		"video_id": "demo-001",
		"language": "en",
		"text": "This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source": "mock"
	},
	"translation": {
		"video_id": "demo-001",
		"language": "es",
		"text": "Transcripción traducida (ES) del video demo-001: This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source_language": "en"
	},
	"summary": {
		"video_id": "demo-001",
		"language": "es",
		"sections": [
			{
				"heading": "Resumen general",
				"text": "El video demo-001 presenta actualizaciones del producto y próximos pasos."
			},
			{
				"heading": "Puntos clave",
				"text": "Se destacó el progreso reciente y la alineación del equipo."
			},
			{
				"heading": "Acciones de seguimiento",
				"text": "Programar una revisión y compartir notas con las partes interesadas."
			}
		]
	}
}
```

### Japanese (`ja`)
```
{
	"input": {
		"video_id": "demo-001",
		"source_language": "en",
		"target_language": "ja"
	},
	"transcript": {
		"video_id": "demo-001",
		"language": "en",
		"text": "This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source": "mock"
	},
	"translation": {
		"video_id": "demo-001",
		"language": "ja",
		"text": "ビデオdemo-001の翻訳済み文字起こし（JA）: This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source_language": "en"
	},
	"summary": {
		"video_id": "demo-001",
		"language": "ja",
		"sections": [
			{
				"heading": "概要",
				"text": "ビデオdemo-001では製品更新と次のステップが説明されています。"
			},
			{
				"heading": "主要なポイント",
				"text": "最近の進捗とチームの整合性が強調されました。"
			},
			{
				"heading": "フォローアップのアクション",
				"text": "レビューを予定し、関係者にメモを共有します。"
			}
		]
	}
}
```

### Portuguese (`pt`)
```
{
	"input": {
		"video_id": "demo-001",
		"source_language": "en",
		"target_language": "pt"
	},
	"transcript": {
		"video_id": "demo-001",
		"language": "en",
		"text": "This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source": "mock"
	},
	"translation": {
		"video_id": "demo-001",
		"language": "pt",
		"text": "Transcrição traduzida (PT) do vídeo demo-001: This is a mock English transcript for video demo-001. It covers product updates and next steps.",
		"source_language": "en"
	},
	"summary": {
		"video_id": "demo-001",
		"language": "pt",
		"sections": [
			{
				"heading": "Resumo geral",
				"text": "O vídeo demo-001 apresenta atualizações do produto e próximos passos."
			},
			{
				"heading": "Principais aprendizados",
				"text": "Foram destacados o progresso recente e o alinhamento da equipe."
			},
			{
				"heading": "Ações de acompanhamento",
				"text": "Agendar uma revisão e compartilhar notas com as partes interessadas."
			}
		]
	}
}
```
