# Troubleshooting

## API startup

Inspect `docker compose logs --tail=100 api`. First builds download Python packages and OCR models; allow network access and sufficient disk space.

## Provider unavailable

Check `/api/providers`. OpenAI requires a key in the API environment and container recreation after configuration changes. Ollama requires a separately running server reachable from the API container.

## UI cannot reach API

Inspect `docker compose ps` and both service logs. The UI shares the API network namespace; recreate both services after network configuration changes.

## Poor answers

Inspect extracted document text and citations. Local hash embeddings match shared terms; include document names and specific terms in questions. Scanned documents depend on OCR quality.
