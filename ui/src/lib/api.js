async function parse(response) {
  const text = await response.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!response.ok) {
    let detail = response.statusText;
    if (body && typeof body === "object") {
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
      }
    } else if (typeof body === "string" && body) {
      detail = body;
    }
    throw new Error(detail);
  }
  return body;
}

export function getHealth() {
  return fetch("/api/health", { cache: "no-store" }).then(parse);
}

export function getProviders() {
  return fetch("/api/providers", { cache: "no-store" }).then(parse);
}

export function listDocuments() {
  return fetch("/api/documents", { cache: "no-store" }).then(parse);
}

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return fetch("/api/documents", { method: "POST", body: form }).then(parse);
}

export function sendChat(message, provider, sessionId) {
  return fetch("/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message,
      provider,
      session_id: sessionId,
    }),
  }).then(parse);
}
