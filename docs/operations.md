# Operations

Start with `docker compose up --build -d`. Inspect status with `docker compose ps` and recent logs with `docker compose logs --tail=100`.

The UI is exposed on port 8080 and the API on port 8000. Health probes use `/api/health`; provider reachability is separately reported by `/api/providers`.

Stop with `docker compose down` to preserve documents. Review the backup procedure in `data-management.md` before upgrades.

For shared deployments, configure access controls and TLS at a reverse proxy and review published ports. Restrict direct API access where appropriate; the application does not enforce user accounts.
