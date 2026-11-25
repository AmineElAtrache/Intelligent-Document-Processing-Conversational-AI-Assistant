# Providers

The default `mock` provider quotes indexed content locally and needs no external model. It is useful for checking extraction and citations.

`openai` reads `OPENAI_API_KEY` and `OPENAI_MODEL` from the API environment. Retrieved document text may leave the machine. Never send a key from the browser.

`ollama` contacts `OLLAMA_BASE_URL` using `OLLAMA_MODEL`. Compose defaults to the host gateway; Ollama itself is not included in the stack.

Set `LLM_PROVIDER` for the default. The UI can choose a provider per question. Provider availability is reported by `/api/providers`; availability does not guarantee a particular model is installed or a request will succeed.
