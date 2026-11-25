"""PaddleOCR on CPU. The engine is created on the first image, not at import."""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

from PIL import Image

from app.config import MAX_PAGES

_ENGINE = None
_LOCK = threading.Lock()


def _build_engine():
    # OneDNN and the model-host check have both wedged CPU containers.
    os.environ.setdefault("FLAGS_use_mkldnn", "0")
    os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
    from paddleocr import PaddleOCR

    attempts = (
        {"use_angle_cls": True, "lang": "en", "use_gpu": False, "show_log": False},
        {"use_angle_cls": True, "lang": "en", "show_log": False},
        {"lang": "en", "use_gpu": False},
        {"lang": "en"},
    )
    errors: list[str] = []
    for kwargs in attempts:
        try:
            return PaddleOCR(**kwargs)
        except (TypeError, ValueError) as exc:
            errors.append(str(exc))
    raise RuntimeError("Could not construct PaddleOCR (" + " | ".join(errors) + ")")


def _engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _build_engine()
    return _ENGINE


def _as_mapping(item):
    if isinstance(item, dict):
        return item
    payload = getattr(item, "json", None)
    if isinstance(payload, dict):
        return payload
    texts = getattr(item, "rec_texts", None)
    if texts is not None:
        return {"rec_texts": texts}
    return None


def _lines(result) -> list[str]:
    if result is None:
        return []
    if not isinstance(result, list):
        mapping = _as_mapping(result)
        if mapping is not None:
            result = [mapping]
        else:
            try:
                result = list(result)
            except TypeError:
                return []
    lines: list[str] = []
    for item in result:
        if item is None:
            continue
        mapping = _as_mapping(item)
        if mapping is not None:
            texts = mapping.get("rec_texts")
            nested = mapping.get("res")
            if texts is None and isinstance(nested, dict):
                texts = nested.get("rec_texts")
            if texts:
                lines.extend(str(text) for text in texts if text)
            continue
        if isinstance(item, list):
            for row in item:
                if not isinstance(row, (list, tuple)) or len(row) < 2:
                    continue
                cell = row[1]
                if isinstance(cell, (list, tuple)) and cell:
                    lines.append(str(cell[0]))
                elif isinstance(cell, str):
                    lines.append(cell)
    return [line.strip() for line in lines if line and line.strip()]


def _recognize(path: str) -> list[str]:
    engine = _engine()
    if hasattr(engine, "ocr"):
        try:
            result = engine.ocr(path, cls=True)
        except TypeError:
            result = engine.ocr(path)
        return _lines(result)
    if hasattr(engine, "predict"):
        return _lines(engine.predict(path))
    raise RuntimeError("This PaddleOCR build has neither ocr() nor predict()")


def ocr_pil(image: Image.Image) -> str:
    """Run CPU PaddleOCR on one PIL image. The first call downloads English models."""
    handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp = handle.name
    handle.close()
    try:
        image.convert("RGB").save(tmp, "PNG")
        with _LOCK:
            lines = _recognize(tmp)
    except Exception as exc:
        raise RuntimeError(f"PaddleOCR failed: {exc}") from exc
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return "\n".join(lines)


def ocr_file(path: Path) -> list[str]:
    pages: list[str] = []
    with Image.open(path) as image:
        frames = getattr(image, "n_frames", 1)
        if frames > MAX_PAGES:
            raise ValueError(f"Image has too many frames (max {MAX_PAGES})")
        for index in range(frames):
            image.seek(index)
            pages.append(ocr_pil(image.copy()))
    return pages
