# Security policy

## Reporting a vulnerability

Do not publish credentials, private documents, or exploit details in public issues. Use GitHub's private vulnerability reporting option on this repository when available. If unavailable, open an issue requesting a private contact channel without including sensitive details.

Include the affected commit, steps to reproduce, expected impact, and a minimal example using synthetic data. There is currently no guaranteed response time or supported release matrix.

## Deployment boundaries

Folio is a local document desk. Review authentication, authorization, TLS, upload limits, and network exposure before making it accessible to other users. Documents and the retrieval index are stored in the configured data directory; protect that directory and its backups.

OpenAI and Ollama providers may send retrieved document text to the configured service. Choose a provider appropriate for the sensitivity of your documents. Keep API keys in environment variables and out of browser requests and source control.
