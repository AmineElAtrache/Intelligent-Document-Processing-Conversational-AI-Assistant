#!/usr/bin/env python3
"""Hit health and one sample-document retrieval. Stdlib only."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request


def fetch(url: str, payload: bytes | None = None, timeout: float = 20) -> tuple[int, bytes]:
    request = urllib.request.Request(url, data=payload)
    if payload is not None:
        request.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()
        raise SystemExit(f"{url} returned {exc.code}: {body.decode()[:500]}") from exc


def wait_health(base: str) -> dict:
    last = "no response"
    for _ in range(60):
        try:
            status, raw = fetch(base + "/api/health", timeout=3)
            body = json.loads(raw)
            if status == 200 and body.get("status") == "ok" and body.get("documents", 0) >= 1:
                return body
            last = json.dumps(body)
        except Exception as exc:  # noqa: BLE001 - keep polling until the desk is up
            last = str(exc)
        time.sleep(2)
    raise SystemExit(f"health check failed: {last}")


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    base = base.rstrip("/")
    status, html = fetch(base + "/", timeout=5)
    page = html.decode("utf-8", errors="replace")
    if status != 200 or "Folio" not in page:
        raise SystemExit("UI did not serve the Folio page")
    health = wait_health(base)
    payload = json.dumps(
        {
            "message": "What is the total due on the Northwind Studio invoice?",
            "provider": "mock",
            "session_id": "smoke",
        }
    ).encode()
    _status, raw = fetch(base + "/api/chat", payload)
    body = json.loads(raw)
    answer = body.get("answer", "")
    citations = body.get("citations") or []
    print(json.dumps({"health": health, "answer": answer, "citations": citations}, indent=2))
    if "4,280.50" not in answer and "4280.50" not in answer:
        raise SystemExit("answer did not include the sample invoice total")
    if not citations or "northwind" not in citations[0].get("document", "").lower():
        raise SystemExit("top citation was not the sample invoice")
    if citations[0].get("page") is None or citations[0].get("chunk") is None:
        raise SystemExit("citation is missing page or chunk")
    print("SMOKE OK")


if __name__ == "__main__":
    main()
