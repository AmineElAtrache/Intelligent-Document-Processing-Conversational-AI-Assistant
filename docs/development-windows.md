# Windows development

Use Docker Desktop with Linux containers for the Compose workflow. From PowerShell at the repository root, run `docker compose up --build`.

For a local API environment:

```powershell
cd api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

OCR also needs Poppler and the native libraries provided by the Docker image. Prefer Docker if native installation fails.

In another terminal, run `npm ci` and `npm run dev` in `ui/`. Use Git Bash or WSL for `scripts/test-offline.sh`; it deletes the Docker data volume.
