"""Local MCP-style client: Change Advisor Agent."""
from __future__ import annotations

import argparse
import textwrap
from typing import Dict, List

import requests

BASE_URL = "http://127.0.0.1:8008"


def _get(path: str) -> Dict:
    resp = requests.get(f"{BASE_URL}{path}", timeout=8)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, body: Dict) -> List[Dict]:
    resp = requests.post(f"{BASE_URL}{path}", json=body, timeout=8)
    resp.raise_for_status()
    return resp.json()


def list_services() -> None:
    services = _get("/services")
    if not services:
        print("No services found. Populate data/runbooks first.")
        return
    print("Known services:")
    for svc in services:
        print(f"- {svc}")


def show_runbook(service: str) -> None:
    data = _get(f"/runbooks/{service}")
    print(f"# Runbook: {data['service']}\n")
    print(data["content"])


def search_runbooks(query: str) -> None:
    hits = _post("/search", {"query": query})
    if not hits:
        print("No matches found.")
        return
    print(f"Top matches for '{query}':")
    for hit in hits:
        excerpt = textwrap.fill(hit["excerpt"], width=80)
        print(f"\n[{hit['service']}]\n{excerpt}")


def analyze_change(service: str, change: str) -> None:
    manifest = _get(f"/services/{service}")
    impact = _get(f"/impact/{service}?change={change}")
    runbook = _get(f"/runbooks/{service}")

    advice = _compose_advice(manifest, impact, runbook, change)
    print(advice)


def _compose_advice(manifest: Dict, impact: Dict, runbook: Dict, change: str) -> str:
    owner = manifest.get("owner", "unknown")
    tier = manifest.get("tier", "n/a")
    ports = ", ".join(str(p) for p in manifest.get("ports", [])) or "n/a"
    deps = impact.get("directly_impacted", []) or ["(none)"]
    notify = impact.get("notify", []) or [owner]
    runbook_summary = runbook.get("content", "").splitlines()[:12]
    summary_text = "\n".join(runbook_summary)

    recommendations = textwrap.dedent(
        f"""
        🚦 Change advisor summary
        Service: {manifest['service']} (Tier: {tier}, Owner: {owner})
        Proposed change: {change}

        Key configs:
          - Runtime: {manifest.get('runtime')}
          - Language: {manifest.get('language')}
          - Ports: {ports}

        Dependencies to coordinate: {', '.join(deps)}
        Notify channels: {', '.join(notify)}

        Runbook briefing:
        {summary_text}

        Recommended steps:
          1. Review runbook alerts or common incidents relevant to the change.
          2. Inform dependents before deployment; confirm their runbooks for cascading effects.
          3. Execute rollout during a window agreed with dependents, following restart/deploy procedures above.
          4. After change, run health checks for each dependent service.
        """
    ).strip()
    return recommendations


def main() -> None:
    parser = argparse.ArgumentParser(description="Local MCP client – Change Advisor Agent")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List known services")

    rb = sub.add_parser("runbook", help="Show full runbook for a service")
    rb.add_argument("service", help="Service key")

    srch = sub.add_parser("search", help="Search runbooks for a keyword")
    srch.add_argument("query", help="Search term")

    impact = sub.add_parser("analyze", help="Generate change advisory for a service")
    impact.add_argument("service", help="Service key")
    impact.add_argument("change", help="Short description of the planned change")

    args = parser.parse_args()

    if args.command == "list":
        list_services()
    elif args.command == "runbook":
        show_runbook(args.service)
    elif args.command == "search":
        search_runbooks(args.query)
    elif args.command == "analyze":
        analyze_change(args.service, args.change)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
