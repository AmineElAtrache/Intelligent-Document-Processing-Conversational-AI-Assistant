# Document privacy

Uploaded files, extracted text, and the FAISS index are stored in `DATA_DIR`. Protect the whole directory and any backups. Preview text and extracted fields are returned to connected browser clients.

The mock provider stays local. OpenAI sends retrieved context to an external service; Ollama sends it to the configured server. Check that service's access controls and retention settings before processing private documents.

The application does not isolate documents by user. Only allow trusted clients to reach the API. When removing a deployment, include its data volume and backups in your retention process.
