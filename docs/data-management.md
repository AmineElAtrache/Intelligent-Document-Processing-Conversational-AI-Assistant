# Data management

`DATA_DIR` holds the document catalog, uploaded files, and FAISS index. Compose mounts the named `idp-data` volume at `/data`.

Stop the stack before taking a consistent filesystem or volume backup. Preserve the complete directory together and protect backups as sensitive documents. Restore into an empty destination while the API is stopped, then start the stack and check catalog counts and a cited query.

`docker compose down` preserves the volume. `docker compose down -v` and the offline smoke script delete it. Session chat memory is not persisted or included in backups.

Changing the embedding implementation requires rebuilding the index so stored vectors match query vectors.
