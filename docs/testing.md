# Testing

Run `npm ci` and `npm run build` in `ui/` for the production frontend build.

With API requirements installed, run `python -m unittest tests.test_offline` in `api/`. These checks cover sample classification, cited retrieval, follow-up questions, and provider refusal without a key.

HTTP tests require `httpx` in addition to the application requirements. Run `python -m unittest tests.test_http` in `api/`. They create a temporary data directory and exercise sample retrieval and binary uploads.

The Docker smoke command `./scripts/test-offline.sh` rebuilds images and deletes the Compose data volume. Only run it with disposable data.
