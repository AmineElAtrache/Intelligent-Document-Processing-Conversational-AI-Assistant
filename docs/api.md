# HTTP API

Interactive schemas are available at `/docs` while the API is running.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Service details and index counts |
| GET | `/api/providers` | Provider availability |
| GET | `/api/documents` | Document catalog |
| GET | `/api/documents/{id}` | One document; 404 if absent |
| POST | `/api/documents` | Multipart upload with field `file` |
| POST | `/api/chat` | Ask a question with citations |

Chat accepts `message`, `provider` (`mock`, `ollama`, `openai`), and `session_id`. Unknown fields are rejected. Messages are limited to 4,000 characters; session identifiers accept letters, digits, underscores, and hyphens up to 80 characters.

Uploads accept PDF, PNG, JPEG, TIFF, BMP, WEBP, DOCX, and TXT up to 20 MiB. Empty or unsupported inputs return 400 and oversized files return 413.
