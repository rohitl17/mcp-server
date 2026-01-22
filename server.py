"""Local runbook & dependency vault server."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RUNBOOK_DIR = DATA_DIR / "runbooks"
MANIFEST_DIR = DATA_DIR / "manifests"
DEPS_FILE = DATA_DIR / "dependencies.json"

app = FastAPI(title="Local Runbook Vault", version="0.1.0")


class Runbook(BaseModel):
    service: str
    content: str


class ServiceManifest(BaseModel):
    service: str
    owner: str
    tier: str
    language: str
    runtime: str
    ports: List[int]
    config: Dict[str, object]


class DependencyRecord(BaseModel):
    service: str
    depends_on: List[str]
    dependents: List[str]


class ImpactResponse(BaseModel):
    service: str
    change_summary: str
    directly_impacted: List[str]
    notify: List[str]
    notes: str


class SearchRequest(BaseModel):
    query: str


class SearchResult(BaseModel):
    service: str
    excerpt: str


def _read_runbook(service: str) -> Runbook:
    path = RUNBOOK_DIR / f"{service}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Runbook not found")
    return Runbook(service=service, content=path.read_text())


def _read_manifest(service: str) -> ServiceManifest:
    path = MANIFEST_DIR / f"{service}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    data = yaml.safe_load(path.read_text()) or {}
    return ServiceManifest(
        service=data.get("service", service),
        owner=data.get("owner", "unknown"),
        tier=data.get("tier", "tier-3"),
        language=data.get("language", "unknown"),
        runtime=data.get("runtime", "unknown"),
        ports=data.get("ports", []),
        config=data.get("config", {}),
    )


def _load_dependencies() -> Dict[str, Dict[str, List[str]]]:
    if not DEPS_FILE.exists():
        return {}
    return json.loads(DEPS_FILE.read_text())


@app.get("/runbooks/{service}", response_model=Runbook)
def get_runbook(service: str) -> Runbook:
    return _read_runbook(service)


@app.get("/services/{service}", response_model=ServiceManifest)
def get_manifest(service: str) -> ServiceManifest:
    return _read_manifest(service)


@app.get("/dependencies", response_model=List[DependencyRecord])
def list_dependencies() -> List[DependencyRecord]:
    deps = _load_dependencies()
    output: List[DependencyRecord] = []
    for svc, record in deps.items():
        output.append(
            DependencyRecord(
                service=svc,
                depends_on=record.get("depends_on", []),
                dependents=record.get("dependents", []),
            )
        )
    return output


@app.get("/impact/{service}", response_model=ImpactResponse)
def simulate_change(service: str, change: str = "config update") -> ImpactResponse:
    deps = _load_dependencies()
    record = deps.get(service)
    if record is None:
        raise HTTPException(status_code=404, detail="Service not tracked")
    notify = record.get("dependents", []) + [record.get("owner", "")] if isinstance(record, dict) else []
    notes = (
        "Review dependent runbooks and inform owners before rollout."
        " Use `impact` endpoint per downstream service as needed."
    )
    return ImpactResponse(
        service=service,
        change_summary=change,
        directly_impacted=record.get("depends_on", []),
        notify=[n for n in notify if n],
        notes=notes,
    )


@app.post("/search", response_model=List[SearchResult])
def search_runbooks(body: SearchRequest) -> List[SearchResult]:
    query = body.query.strip().lower()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results: List[SearchResult] = []
    for path in RUNBOOK_DIR.glob("*.md"):
        text = path.read_text()
        if query in text.lower():
            snippet = _build_excerpt(text, query)
            results.append(SearchResult(service=path.stem, excerpt=snippet))
    return results[:10]


def _build_excerpt(text: str, query: str, window: int = 80) -> str:
    lower = text.lower()
    idx = lower.find(query)
    if idx == -1:
        return text[:window] + ("..." if len(text) > window else "")
    start = max(0, idx - window)
    end = min(len(text), idx + len(query) + window)
    excerpt = text[start:end]
    if start > 0:
        excerpt = "..." + excerpt
    if end < len(text):
        excerpt += "..."
    return excerpt


@app.get("/services", response_model=List[str])
def list_services() -> List[str]:
    return sorted({path.stem for path in RUNBOOK_DIR.glob("*.md")})


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8008, reload=False)
