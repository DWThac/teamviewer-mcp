"""TeamViewer Reporting MCP server.

A read-only Model Context Protocol server that exposes the TeamViewer
Web API to LLM clients (Claude, Cursor, Continue, etc.) as a small,
clearly-scoped set of tools.

Auth
----
Set the ``TEAMVIEWER_TOKEN`` environment variable to a script token
from the TeamViewer Management Console (Apps & Tokens). The token is
read on the first tool call, so the module is safe to import without
it set — useful for tests and tooling.

Tools
-----
``tv_whoami``, ``tv_connection_report``, ``tv_list_users``,
``tv_list_devices``, ``tv_list_groups``, ``tv_list_contacts``,
``tv_list_service_cases``.

Run
---
::

    TEAMVIEWER_TOKEN=... python teamviewer_mcp.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

__version__ = "0.1.0"
__all__ = [
    "tv_whoami",
    "tv_connection_report",
    "tv_list_users",
    "tv_list_devices",
    "tv_list_groups",
    "tv_list_contacts",
    "tv_list_service_cases",
]

API_BASE = "https://webapi.teamviewer.com/api/v1"
USER_AGENT = f"teamviewer-mcp/{__version__}"
REQUEST_TIMEOUT_S = 30.0
ERROR_BODY_SNIPPET = 120  # chars retained from non-JSON error bodies

mcp = FastMCP("teamviewer-reporting")

# Lazily-built HTTP client. Constructed on first tool call so that
# importing the module never reads the token or opens sockets.
_client: httpx.Client | None = None


# ─── HTTP plumbing ─────────────────────────────────────────────────────────


def _build_client() -> httpx.Client:
    """Construct the shared httpx.Client; raise if the token is missing."""
    token = os.environ.get("TEAMVIEWER_TOKEN")
    if not token:
        raise RuntimeError(
            "TEAMVIEWER_TOKEN env var is not set. "
            "Generate a script token in the TeamViewer Management Console "
            "(Apps & Tokens) and pass it via the MCP server's env block."
        )
    return httpx.Client(
        base_url=API_BASE,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        timeout=REQUEST_TIMEOUT_S,
    )


def _get_client() -> httpx.Client:
    """Return the shared client, building it on first use."""
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def _format_error(r: httpx.Response, path: str) -> str:
    """Build a non-leaky error string from a 4xx/5xx response.

    Prefers TeamViewer's structured error fields (which describe API
    state, not request input, so they don't echo any caller-supplied
    customer data). Falls back to a short snippet of the raw body when
    the response isn't the expected JSON shape.
    """
    try:
        body = r.json()
    except ValueError:
        body = None

    if isinstance(body, dict) and ("error" in body or "error_description" in body):
        err = body.get("error") or "?"
        desc = body.get("error_description") or ""
        code = body.get("error_code")
        code_part = f" ({code})" if code is not None else ""
        sep = " — " if desc else ""
        return (
            f"TeamViewer API {r.status_code} on GET {path}: {err}{code_part}{sep}{desc}"
        )

    text = r.text or ""
    snippet = text[:ERROR_BODY_SNIPPET]
    return (
        f"TeamViewer API {r.status_code} on GET {path}: "
        f"<unstructured body, {len(text)} chars; first {ERROR_BODY_SNIPPET}: {snippet!r}>"
    )


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET ``path`` from the TeamViewer API and return parsed JSON.

    Rejects anything that isn't a single-leading-slash relative path so
    that a future caller can't accidentally escape ``API_BASE``.
    """
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError(f"path must be a single-slash, relative path; got {path!r}")

    clean = {k: v for k, v in (params or {}).items() if v is not None}
    r = _get_client().get(path, params=clean)
    if r.status_code >= 400:
        raise RuntimeError(_format_error(r, path))
    return r.json()


# ─── MCP tools ─────────────────────────────────────────────────────────────


@mcp.tool()
def tv_whoami() -> Any:
    """Return the TeamViewer account the configured token belongs to.

    Useful as a first call to confirm the token is valid before pulling data.
    """
    return _get("/account")


@mcp.tool()
def tv_connection_report(
    from_date: str | None = None,
    to_date: str | None = None,
    username: str | None = None,
    offset_id: str | None = None,
) -> Any:
    """Connection (session) report — the main reporting endpoint.

    Returns up to 1000 records per call. To page beyond that, pass the
    last record's ``id`` as ``offset_id`` on the next call.

    Args:
        from_date: ISO-8601 start, e.g. ``2026-04-01T00:00:00Z``.
                   Omit for the most recent records.
        to_date:   ISO-8601 end,   e.g. ``2026-04-29T23:59:59Z``.
        username:  Filter by the TeamViewer account name that initiated
                   the session.
        offset_id: Continuation token from the previous page's last record.
    """
    return _get(
        "/reports/connections",
        {
            "from_date": from_date,
            "to_date": to_date,
            "username": username,
            "offset_id": offset_id,
        },
    )


@mcp.tool()
def tv_list_users() -> Any:
    """List company users. Returned fields depend on licence and token scope."""
    return _get("/users")


@mcp.tool()
def tv_list_devices() -> Any:
    """List managed devices in the company account."""
    return _get("/devices")


@mcp.tool()
def tv_list_groups() -> Any:
    """List groups available to this account."""
    return _get("/groups")


@mcp.tool()
def tv_list_contacts() -> Any:
    """List entries from the user's Computers & Contacts list."""
    return _get("/contacts")


@mcp.tool()
def tv_list_service_cases() -> Any:
    """List Assist service cases / sessions.

    Some accounts expose ``/servicecases`` in place of ``/sessions``.
    If this tool returns 404, swap the path and please open a PR with
    the variant for your licence.
    """
    return _get("/sessions")


# ─── Entrypoint ────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entrypoint: validate config, then start the stdio MCP server."""
    if not os.environ.get("TEAMVIEWER_TOKEN"):
        print(
            "TEAMVIEWER_TOKEN env var is not set. "
            "Generate a script token in the TeamViewer Management Console "
            "and set it in the MCP server's env block before launching.",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run()


if __name__ == "__main__":
    main()
