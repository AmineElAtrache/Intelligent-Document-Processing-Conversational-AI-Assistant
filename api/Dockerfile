FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FLAGS_use_mkldnn=0 \
    OMP_NUM_THREADS=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    DATA_DIR=/data

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
        libgl1 \
        libgfortran5 \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 5 -r requirements.txt

# English detection, recognition, and angle models. Fetch them without
# initializing Paddle, which can segfault during a Docker build.
RUN python - << 'PY'
import tarfile
import urllib.request
from pathlib import Path

jobs = {
    "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar":
        "/root/.paddleocr/whl/det/en/en_PP-OCRv3_det_infer",
    "https://paddleocr.bj.bcebos.com/PP-OCRv4/english/en_PP-OCRv4_rec_infer.tar":
        "/root/.paddleocr/whl/rec/en/en_PP-OCRv4_rec_infer",
    "https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar":
        "/root/.paddleocr/whl/cls/ch_ppocr_mobile_v2.0_cls_infer",
}
suffixes = (".pdmodel", ".pdiparams", ".pdiparams.info")
for url, dest in jobs.items():
    folder = Path(dest)
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "model.tar"
    urllib.request.urlretrieve(url, archive)
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            filename = None
            for suffix in suffixes:
                if member.name.endswith(suffix):
                    filename = "inference" + suffix
            if filename is None:
                continue
            source = bundle.extractfile(member)
            if source is None:
                continue
            (folder / filename).write_bytes(source.read())
    archive.unlink()
print("paddleocr-models-ready")
PY

COPY app ./app
COPY samples ./samples

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
