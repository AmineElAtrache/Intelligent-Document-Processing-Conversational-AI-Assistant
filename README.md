# Folio

Folio is a small document desk. It takes PDF, image, scan, DOCX, and text files, reads them (PaddleOCR for images and pages without a text layer), chunks and embeds them into FAISS, and answers questions with citations. A Svelte page shows the upload list, extracted fields, and the chat.

The first boot does not need a GPU or an OpenAI key. Two sample documents are seeded into the index when the data volume is empty, and the default provider quotes those chunks on the machine.

## One-command test

From this directory, with Docker running:

```bash
./scripts/test-offline.sh
```

That command checks the Compose file, rebuilds the CPU images, recreates the data volume, and asks the seeded Northwind invoice for its total. It forces `LLM_PROVIDER=mock` and an empty `OPENAI_API_KEY`. Ollama is not contacted. Success prints `SMOKE OK`.

Then open:

- UI: http://127.0.0.1:8080
- API docs: http://127.0.0.1:8000/docs

The test script deletes the `idp-data` volume so the seed runs again. Use `docker compose up --build` when you want to keep uploaded documents.

## Run

```bash
docker compose up --build
```

The image is CPU-only. Compose does not reserve a GPU. PaddleOCR is constructed with the CPU engine. The UI container shares the API container's network namespace, and nginx proxies `/api` to `127.0.0.1:8000`.

To call OpenAI, put a key in the environment (never in source) and recreate the API container:

```bash
export OPENAI_API_KEY=your_key_here
export LLM_PROVIDER=openai
docker compose up --build
```

The browser only sends the provider name. The API reads `OPENAI_API_KEY` itself. Requests that try to include a key are rejected.

Ollama is optional and is not installed in the image. If a server is already running on the host, the API reaches it at `OLLAMA_BASE_URL` (default `http://host.docker.internal:11434`). Choose Ollama in the page. If nothing is listening, the chat returns an error and the mock provider still works.

## What the page does

- Upload PDF, PNG, JPEG, TIFF, BMP, WEBP, DOCX, or TXT (20 MB).
- List documents and show the keyword type, dates, amounts, and names.
- Chat across the index. Each reply cites a document, a page, and a chunk.

Sample files live in `api/samples/`. Startup indexes `northwind-invoice.txt` and `reading-room-letter.txt` when the catalog is empty. `northwind-invoice.pdf`, `northwind-invoice.docx`, and `cafe-atlas-receipt.png` are extra fixtures for upload. The image build downloads the English PaddleOCR models, so reading the receipt does not need another download and does not need a GPU.

## Local run without Compose

```bash
cd api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

```bash
cd ui
npm install
npm run dev
```

The dev server proxies `/api` to port 8000. Open http://127.0.0.1:5173.

`python -m unittest tests.test_offline` in `api/` checks field extraction and one FAISS retrieval against the samples.

## Stack

| Piece | Choice |
| --- | --- |
| API | Python, FastAPI |
| UI | Svelte, Vite, nginx |
| Retrieval | LangChain text splitter, embeddings interface, FAISS, LCEL prompt |
| OCR | PaddleOCR 2.9.1 with PaddlePaddle 2.6.2, CPU |
| Chat | Mock reader by default, LangChain ChatOllama, or LangChain ChatOpenAI |
| Run | Docker Compose, one API service and one UI service |

PaddleOCR 3.x pulls PaddleX and a much larger model stack. This image pins the last classic 2.9.1 release so it can boot on CPU without a GPU. The Docker build downloads the small English PP-OCR models into the image.

Embeddings are a local signed feature hash (384 dimensions), not a neural model. That keeps the seed index usable with no model download and no API key. It favors shared words and phrases. Swap `LocalHashEmbeddings` if you later want a neural embedder; the FAISS index would need to be rebuilt, because the vectors would no longer match.

Document type is a keyword score. A line that is only the word invoice, receipt, or contract counts on its own. Dates, amounts, and names come from patterns and labels. **LayoutLM is not installed.** A transformer document classifier would add a large torch stack and model weights, and this version stays small enough to boot without that.

Chat memory is kept in the API process for the session id. It is not written to disk.

## Architecture references

These projects were read as architecture references. Folio is a separate codebase: nothing from them is vendored, and their source was not copied.

| Project | License | What it informed |
| --- | --- | --- |
| [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Apache-2.0 | CPU OCR for images and scanned PDF pages |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | MIT | Splitter, embeddings interface, FAISS vector store, LCEL chat prompt |
| [facebookresearch/faiss](https://github.com/facebookresearch/faiss) | MIT | Local similarity index |
| [ollama/ollama](https://github.com/ollama/ollama) | MIT | Optional local model server. Not bundled |
| [GouravJr/rag-document-intelligence](https://github.com/GouravJr/rag-document-intelligence) | MIT | Shape of a small FastAPI ingest, retrieve, and field-extraction service |
| [SwastikPandey1024/DocMind](https://github.com/SwastikPandey1024/DocMind) | MIT | API plus web UI, OCR then FAISS, Ollama or OpenAI switch, Compose. The README currently titles that app DocuChat |

## Environment

| Variable | Default | Role |
| --- | --- | --- |
| `LLM_PROVIDER` | `mock` | Default provider. The page can override it per question |
| `OPENAI_API_KEY` | empty | Required only for the OpenAI provider |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` in Compose | Ollama server |
| `OLLAMA_MODEL` | `llama3.2` | Ollama chat model |
| `DATA_DIR` | `/data` in Compose | Catalog, uploads, and FAISS index |

See `.env.example`. Compose reads those names from the shell or a `.env` file next to `docker-compose.yml`.
