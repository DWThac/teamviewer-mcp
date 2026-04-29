"""TeamViewer Reporting MCP server.

Exposes read-only TeamViewer Web API endpoints as MCP tools so Claude can
pull connection reports, users, devices, groups, contacts, and service cases.

Auth: set env var TEAMVIEWER_TOKEN to a script token from
TeamViewer Management Console -> Apps & Tokens.
"""
from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = "https://webapi.teamviewer.com/api/v1"

token = os.environ.get("TEAMVIEWER_TOKEN")
if not token:
    print(
        "TEAMVIEWER_TOKEN env var is not set. "
        "Generate a script token in TeamViewer Management Console "
        "(Apps & Tokens) and set it in the MCP server config.",
        file=sys.stderr,
    )
    sys.exit(1)

client = httpx.Client(
    base_url=API_BASE,
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    timeout=30.0,
)

mcp = FastMCP("teamviewer-reporting")


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    r = client.get(path, params=clean)
    if r.status_code >= 400:
        raise RuntimeError(
            f"TeamViewer API {r.status_code} on GET {path}: {r.text}"
        )
    return r.json()


@mcp.tool()
def tv_whoami() -> Any:
    """Sanity check. Returns the TeamViewer account the token belongs to."""
    return _get("/account")


@mcp.tool()
def tv_connection_report(
    from_date: str | None = None,
    to_date: str | None = None,
    username: str | None = None,
    offset_id: str | None = None,
) -> Any:
    """Connection (session) report.

    Args:
        from_date: ISO-8601 start, e.g. '2026-04-01T00:00:00Z'.
        to_date:   ISO-8601 end,   e.g. '2026-04-29T23:59:59Z'.
        username:  Optional filter by the TeamViewer account that initiated the session.
        offset_id: Pass the last record's id to page beyond 1000 results.
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
    """List company users (id, email, name, active, permissions)."""
    return _get("/users")


@mcp.tool()
def tv_list_devices() -> Any:
    """List managed devices (alias, online_state, groupid, remotecontrol_id)."""
    return _get("/devices")


@mcp.tool()
def tv_list_groups() -> Any:
    """List groups available to this account."""
    return _get("/groups")


@mcp.tool()
def tv_list_contacts() -> Any:
    """List Computers & Contacts entries."""
    return _get("/contacts")


@mcp.tool()
def tv_list_service_cases() -> Any:
    """List Assist service cases / sessions."""
    return _get("/sessions")


if __name__ == "__main__":
    mcp.run()
