# Sample documents

Startup seeds `northwind-invoice.txt` and `reading-room-letter.txt` when the catalog is empty. These provide predictable retrieval examples without OCR or external providers.

Ask: `What is the total due on the Northwind Studio invoice?` The sample amount is `4,280.50 MAD`. A follow-up `When is it due?` should identify `11 April 2026`.

Additional PDF, DOCX, and PNG fixtures in `api/samples/` exercise binary upload and OCR. Use synthetic fixtures when filing issues; never attach private customer documents.
