# Current limitations

- Embeddings use signed feature hashing rather than a neural semantic model.
- Classification and field extraction use keyword and pattern rules.
- LayoutLM is not installed.
- OCR ships English models; other languages and low-quality scans may produce poor results.
- Chat memory is process-local and disappears on restart.
- The service has no built-in user authentication or per-user document isolation.
- File uploads are limited to 20 MiB and extraction has a 30-page limit.

Validate extracted fields and cited answers against original documents before relying on them.
