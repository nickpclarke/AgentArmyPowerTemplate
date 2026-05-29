"""board-sync connectors — fetch live work items from a board system and flatten them
into the field shape the vended adapter expects. GitHub Projects v2 is wired live
(token resolved from Key Vault, like backend-core); Linear is sample-only here (no
workspace key) — its connector is the same shape, ready for a key.

Keys stay out of source: GH_TOKEN env, else akv:GithubPAT via DefaultAzureCredential.
"""
from __future__ import annotations

import json
import os
import urllib.request

_GH_GRAPHQL = "https://api.github.com/graphql"
_PROJECTS_QUERY = """
query {
  viewer { login projectsV2(first: %d) { nodes {
    number title
    items(first: %d) { nodes {
      id
      content { __typename ... on Issue {
        number title body url createdAt updatedAt state
        labels(first: 10) { nodes { name } }
        assignees(first: 5) { nodes { login } }
        milestone { title } } }
      fieldValues(first: 20) { nodes {
        __typename
        ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
        ... on ProjectV2ItemFieldIterationValue { title field { ... on ProjectV2FieldCommon { name } } } } }
    } }
  } } }
}"""


def github_token() -> str:
    """GH_TOKEN env, else Key Vault secret GithubPAT (DefaultAzureCredential)."""
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    vault = os.environ.get("AZURE_KEYVAULT_URL", "https://akv01-agentarmy.vault.azure.net")
    name = os.environ.get("GITHUB_PAT_SECRET", "GithubPAT")
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    return SecretClient(vault_url=vault, credential=DefaultAzureCredential()).get_secret(name).value or ""


def _flatten_item(item: dict) -> dict | None:
    content = item.get("content") or {}
    if content.get("__typename") != "Issue":
        return None
    fv = {n.get("field", {}).get("name", ""): (n.get("name") or n.get("title"))
          for n in item.get("fieldValues", {}).get("nodes", []) if n.get("field")}
    return {
        "id": item.get("id"), "number": content.get("number"), "title": content.get("title"),
        "body": content.get("body"), "url": content.get("url"),
        "createdAt": content.get("createdAt"), "updatedAt": content.get("updatedAt"),
        "state": content.get("state"), "status": fv.get("Status"),
        "iteration": fv.get("Iteration") or fv.get("Sprint"),
        "labels": [n["name"] for n in content.get("labels", {}).get("nodes", [])],
        "assignees": [n["login"] for n in content.get("assignees", {}).get("nodes", [])],
        "milestone": (content.get("milestone") or {}).get("title"),
    }


def github_v2_items(projects: int = 2, per_project: int = 20) -> list[dict]:
    """Live: fetch Projects v2 items for the authenticated user, flattened to the
    adapter's source-field shape. Proven against the AgentArmy board (#1)."""
    body = json.dumps({"query": _PROJECTS_QUERY % (projects, per_project)}).encode()
    req = urllib.request.Request(  # nosemgrep — fixed GitHub GraphQL endpoint
        _GH_GRAPHQL, data=body,
        headers={"Authorization": f"bearer {github_token()}", "Content-Type": "application/json",
                 "User-Agent": "agentarmy-board-sync"})
    with urllib.request.urlopen(req, timeout=30) as r:  # nosemgrep — fixed endpoint
        data = json.load(r)
    if data.get("errors"):
        raise RuntimeError(f"GitHub GraphQL: {data['errors']}")
    out: list[dict] = []
    for p in data["data"]["viewer"]["projectsV2"]["nodes"]:
        for it in p["items"]["nodes"]:
            flat = _flatten_item(it)
            if flat:
                out.append(flat)
    return out
