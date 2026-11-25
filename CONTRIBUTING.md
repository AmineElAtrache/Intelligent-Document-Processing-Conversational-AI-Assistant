# Contributing to Folio

Open an issue describing the problem or proposed behavior before starting a large change. Include sample input with personal information removed and the expected result.

## Development

Follow the local setup in README.md. Use Python 3.11 and Node.js 22. Install frontend dependencies with `npm ci` in `ui/` to respect the lockfile.

Before submitting a change:

- Run `npm run build` in `ui/`.
- Run `python -m compileall -q api/app api/tests scripts` from the repository root.
- With API dependencies installed, run `python -m unittest tests.test_offline` in `api/`.
- For ingestion or provider changes, run the Docker smoke check on disposable data. `scripts/test-offline.sh` deletes the Compose data volume.

## Pull requests

Keep each change focused and explain the problem, resulting behavior, and validation. Add regression coverage for behavior changes. Include screenshots for visible UI changes and document new environment variables in both README.md and `.env.example`.

Never commit credentials, private documents, generated indexes, or local data. Keep commit timestamps accurate and use messages that describe the change.
