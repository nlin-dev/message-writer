#!/usr/bin/env python3
"""Grounding evaluation harness. Produces a JSON report for a message's claim support."""

import argparse
import json
import sys

import httpx


def evaluate_grounding(message_id: int, api_url: str) -> dict:
    try:
        resp = httpx.get(f"{api_url}/messages/{message_id}", timeout=10)
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": f"Cannot connect to API at {api_url}"}
    except httpx.HTTPError as e:
        return {"error": str(e)}

    if resp.status_code == 404:
        return {"error": f"Message {message_id} not found"}
    if resp.status_code >= 400:
        return {"error": f"API returned {resp.status_code}"}

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return {"error": "Invalid JSON response from API"}
    versions = data.get("versions", [])
    if not versions:
        return {"error": f"Message {message_id} has no versions"}

    latest = max(versions, key=lambda v: v["version_number"])

    supported_claims = latest.get("claims", [])
    dropped_claims = latest.get("dropped_claims", [])
    all_claims = supported_claims + dropped_claims
    total = len(all_claims)
    supported = len(supported_claims)
    dropped = len(dropped_claims)

    failures = [
        {"claim_text": c["text"], "status": c["status"], "warning": c.get("warning")}
        for c in dropped_claims
    ]

    return {
        "message_id": message_id,
        "version": latest["version_number"],
        "pass": dropped == 0,
        "total_claims": total,
        "supported": supported,
        "dropped": dropped,
        "support_rate": round(supported / total, 4) if total > 0 else 1.0,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate grounding for a message")
    parser.add_argument("--message-id", type=int, required=True)
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    result = evaluate_grounding(args.message_id, args.api_url)

    if "error" in result:
        print(json.dumps({"error": result["error"]}))
        return 2

    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
