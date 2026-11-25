# Docker build contexts

Compose builds the API from `api/` and the UI from `ui/`. Each directory has its own `.dockerignore`; root ignore rules do not automatically apply to these contexts.

Keep API data, virtual environments, secrets, and Python caches out of the API context. Keep local node_modules, generated dist files, and environment files out of the UI context.

The UI image installs from the lockfile and builds assets inside its build stage. The API image downloads OCR models during build. Rebuild after changing dependencies or model setup.
