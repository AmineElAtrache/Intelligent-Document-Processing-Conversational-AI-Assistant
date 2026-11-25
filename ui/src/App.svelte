<script>
  import { onMount } from "svelte";
  import {
    getHealth,
    getProviders,
    listDocuments,
    sendChat,
    uploadDocument,
  } from "./lib/api.js";

  let documents = $state([]);
  let selectedId = $state("");
  let health = $state(null);
  let providers = $state(null);
  let provider = $state("mock");
  let messages = $state([]);
  let draft = $state("");
  let busy = $state(false);
  let uploading = $state(false);
  let error = $state("");

  const sessionId =
    globalThis.crypto?.randomUUID?.() ?? `desk-${Date.now()}`;
  const prompts = [
    "What is the total due on the Northwind Studio invoice?",
    "Who is the invoice billed to?",
    "When is it due?",
  ];

  let selected = $derived(documents.find((doc) => doc.id === selectedId) ?? null);
  let providerHint = $derived(providers?.[provider]?.detail ?? "");

  function selectInvoice(docs) {
    const invoice = docs.find((doc) => doc.doc_type === "invoice");
    return (invoice ?? docs[0])?.id ?? "";
  }

  async function refresh(preferId = "") {
    const [docs, status] = await Promise.all([listDocuments(), getHealth()]);
    documents = docs;
    health = status;
    if (preferId && docs.some((doc) => doc.id === preferId)) selectedId = preferId;
    else if (!selectedId || !docs.some((doc) => doc.id === selectedId)) {
      selectedId = selectInvoice(docs);
    }
  }

  async function onFile(event) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = "";
    if (!file) return;
    uploading = true;
    error = "";
    try {
      const saved = await uploadDocument(file);
      await refresh(saved.id);
    } catch (err) {
      error = err.message;
    } finally {
      uploading = false;
    }
  }

  async function ask(text = draft) {
    const message = text.trim();
    if (!message || busy) return;
    if (message.length > 4000) {
      error = "Questions must be 4,000 characters or fewer.";
      return;
    }
    draft = "";
    messages = [...messages, { role: "user", text: message }];
    busy = true;
    error = "";
    try {
      const reply = await sendChat(message, provider, sessionId);
      messages = [
        ...messages,
        {
          role: "assistant",
          text: reply.answer,
          provider: reply.provider,
          citations: reply.citations ?? [],
        },
      ];
    } catch (err) {
      error = err.message;
    } finally {
      busy = false;
      if (error && !draft) draft = message;
    }
  }

  function onKey(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      ask();
    }
  }

  function openCitation(citation) {
    if (documents.some((doc) => doc.id === citation.doc_id)) {
      selectedId = citation.doc_id;
    }
  }

  onMount(async () => {
    try {
      await refresh();
      providers = await getProviders();
      if (providers?.default) provider = providers.default;
    } catch (err) {
      error = err.message;
    }
  });
</script>

<main class="desk">
  <header>
    <div class="brand">
      <div class="mark" aria-hidden="true"></div>
      <div>
        <p class="eyebrow">Document desk</p>
        <h1>Folio</h1>
      </div>
    </div>
    <label class="provider">
      <span>Answer with</span>
      <select bind:value={provider} aria-label="Answer with" disabled={busy}>
        <option value="mock">Mock, on this machine</option>
        <option value="ollama">Ollama, if it is running</option>
        <option value="openai">OpenAI, if a key is set</option>
      </select>
      <small class="hint">{providerHint}</small>
    </label>
  </header>

  {#if error}
    <p class="banner" role="alert">{error}</p>
  {/if}

  <div class="layout">
    <section class="panel">
      <h2>Documents</h2>
      <label class="file">
        <input
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp,.webp,.docx,.txt,application/pdf,text/plain"
          onchange={onFile}
          disabled={uploading}
          aria-label="Upload a document"
        />
      </label>
      <p class="muted" role="status">{uploading ? "Reading the file…" : "PDF, image, scan, docx, or txt. Up to 20 MB."}</p>
      <ul class="doc-list">
        {#each documents as doc (doc.id)}
          <li>
            <button
              type="button"
              class:active={doc.id === selectedId}
              aria-pressed={doc.id === selectedId}
              onclick={() => (selectedId = doc.id)}
            >
              <strong>{doc.filename}</strong>
              <span class="muted">{doc.doc_type} · {doc.pages} page{doc.pages === 1 ? "" : "s"}</span>
            </button>
          </li>
        {/each}
      </ul>
    </section>

    <section class="panel">
      <h2>Extracted fields</h2>
      {#if selected}
        <p>
          <span class="stamp">{selected.doc_type}</span>
        </p>
        <p class="muted">
          Keyword score {selected.type_score}. LayoutLM is not installed.
          {selected.ocr_used ? "PaddleOCR read this file." : "Text was read directly."}
          {selected.chunks} chunk{selected.chunks === 1 ? "" : "s"}.
        </p>
        <div class="fields">
          {#each [
            ["Dates", selected.fields.dates],
            ["Amounts", selected.fields.amounts],
            ["Names", selected.fields.names],
          ] as [label, values]}
            <div class="field">
              <h3>{label}</h3>
              {#if values?.length}
                <ul>
                  {#each values as value}
                    <li>{value}</li>
                  {/each}
                </ul>
              {:else}
                <p class="muted">None found</p>
              {/if}
            </div>
          {/each}
        </div>
        <h3 class="eyebrow">Indexed text</h3>
        <pre class="preview">{selected.preview}</pre>
      {:else}
        <p class="muted">No documents yet.</p>
      {/if}
    </section>

    <section class="panel chat">
      <h2>Chat</h2>
      <div class="prompts">
        {#each prompts as prompt}
          <button type="button" onclick={() => ask(prompt)} disabled={busy}>{prompt}</button>
        {/each}
      </div>
      <div class="log" role="log" aria-label="Conversation" aria-live="polite" aria-busy={busy}>
        {#if messages.length === 0}
          <p class="muted">Ask about the seeded Northwind invoice. Citations name the document, page, and chunk.</p>
        {/if}
        {#each messages as message, index (index)}
          <article class="bubble {message.role}">
            <p>{message.text}</p>
            {#if message.citations?.length}
              <div class="citations">
                {#each message.citations as citation}
                  <button type="button" onclick={() => openCitation(citation)}>
                    {citation.document} · page {citation.page} · chunk {citation.chunk}
                    <small>{citation.excerpt}</small>
                  </button>
                {/each}
              </div>
            {/if}
          </article>
        {/each}
      </div>
      <form class="composer" onsubmit={(event) => { event.preventDefault(); ask(); }}>
        <label>
          <span class="eyebrow">Question</span>
          <textarea
            bind:value={draft}
            onkeydown={onKey}
            placeholder="Ask about a date, amount, or name"
            aria-label="Question"
            maxlength="4000"
          ></textarea>
        </label>
        <button class="send" type="submit" disabled={busy || !draft.trim()}>
          {busy ? "Looking…" : "Ask"}
        </button>
      </form>
    </section>
  </div>

  <footer class="status">
    {#if health}
      {health.documents} documents, {health.chunks} chunks.
      Embeddings: {health.embeddings}. Classifier: {health.classifier}.
      OpenAI key on the API: {health.openai_configured ? "set" : "not set"}.
      Ollama is not in the image.
    {:else}
      Waiting for the API.
    {/if}
  </footer>
</main>
