# Architecture

The Svelte UI calls `/api` through nginx. The UI container shares the API network namespace, so nginx reaches FastAPI on loopback port 8000.

Uploads flow through extraction, optional PaddleOCR, keyword field classification, chunking, local hash embeddings, and a persisted FAISS index. The catalog and uploads use `DATA_DIR`.

Chat retrieves chunks and passes them to the selected mock, Ollama, or OpenAI provider. Responses carry document, page, and chunk citations. Conversation memory lives in the API process and is lost on restart.
