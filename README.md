# Local Runbook & Dependency Vault

A lightweight FastAPI server that mimics a Model Context Protocol (MCP) data source for design-review copilots. It keeps everything on disk—Markdown runbooks, YAML service manifests, and a JSON dependency graph—so you can explore MCP-style integrations without hitting external APIs.

## Features
- **Runbook retrieval** – `GET /runbooks/{service}` returns Markdown runbooks from `data/runbooks/`.
- **Service manifests** – `GET /services/{service}` reads YAML manifests (`owner`, `tier`, `config`, etc.).
- **Dependency graph** – `GET /dependencies` and `GET /impact/{service}` expose upstream/downstream relationships.
- **Full-text search** – `POST /search` finds runbooks containing a query string and returns excerpts.
- **Service catalog** – `GET /services` lists every service with a runbook.
- **Local-only data** – everything lives under `./data`, so the server runs air-gapped or offline.

## Project layout
```
mcp_server/
├── data/
│   ├── runbooks/
│   │   ├── payment-service.md
│   │   └── notifications.md
│   ├── manifests/
│   │   ├── payment-service.yaml
│   │   └── notifications.yaml
│   └── dependencies.json
├── server.py
└── README.md
```

## Requirements
- Python 3.10+
- `fastapi`, `uvicorn`, `pyyaml`

Install dependencies:
```bash
pip install fastapi uvicorn pyyaml
```

## Running the server
```bash
cd mcp_server
python server.py
```
The API listens on `http://127.0.0.1:8008`. Visit `http://127.0.0.1:8008/docs` for Swagger UI.

## Change Advisor client (example MCP consumer)
`client.py` simulates an AI agent that consumes the local vault:

```bash
python client.py list
python client.py runbook payment-service
python client.py analyze payment-service "Rotate PSP credentials"
```

Under the hood it uses the same resources your MCP-compatible assistant would call: runbook lookup, manifest info, dependency impact, and search.

## Example requests
- Runbook:
  ```bash
  curl http://127.0.0.1:8008/runbooks/payment-service
  ```
- Manifest:
  ```bash
  curl http://127.0.0.1:8008/services/payment-service
  ```
- Search:
  ```bash
  curl -X POST http://127.0.0.1:8008/search -H 'Content-Type: application/json' -d '{"query": "PSP"}'
  ```

## Extending / integrating with MCP
- Replace the FastAPI layer with an MCP server adapter (e.g., `mcp.server.Server`) while reusing the filesystem logic in `server.py`.
- Wire MCP resources/actions to the helper functions (`_read_runbook`, `_read_manifest`, etc.).
- Use file-system watchers (e.g., `watchfiles`) to emit MCP notifications when runbooks change.

## Customizing data
- Add more Markdown files under `data/runbooks/` and YAML manifests under `data/manifests/`.
- Update `data/dependencies.json` to reflect relationships.
- The server auto-discovers new files without code changes.

This repo gives you a realistic playground to experiment with MCP client-server flows while keeping everything local and deterministic.
