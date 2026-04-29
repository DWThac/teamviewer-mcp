# 📡 TeamViewer MCP Server

> A minimal **read-only [Model Context Protocol](https://modelcontextprotocol.io) server** for the [TeamViewer Web API](https://webapi.teamviewer.com/api/v1/docs/index).

![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![MCP](https://img.shields.io/badge/mcp-compliant-blueviolet)

---

> [!WARNING]
> **Unofficial & Experimental**
> This is an **unofficial** MCP server created for testing and experimentation purposes. It is **not** affiliated with, endorsed by, or supported by TeamViewer. Use at your own risk. TeamViewer is not responsible for any issues, data loss, or consequences arising from the use of this tool.

Plug it into Claude Code (or any MCP client) and pull live reports from your TeamViewer account in plain English.

## What you get

Seven tools, all read-only, all just thin wrappers over a single `Authorization: Bearer <script-token>` header:

| MCP tool | TeamViewer endpoint | Purpose |
|---|---|---|
| `tv_whoami` | `GET /account` | Sanity check — confirms your token works, returns account/email/company/license. |
| `tv_connection_report` | `GET /reports/connections` | The main reporting endpoint. Optional `from_date`, `to_date`, `username`, `offset_id` (paging). |
| `tv_list_users` | `GET /users` | Company users (id, email, name). |
| `tv_list_devices` | `GET /devices` | Managed devices (alias, online state, group, TeamViewer ID). |
| `tv_list_groups` | `GET /groups` | Groups available to this account. |
| `tv_list_contacts` | `GET /contacts` | Computers & Contacts entries. |
| `tv_list_service_cases` | `GET /sessions` | Assist service cases / sessions. |

There are no write/destructive tools. Worst case, the server can read what your token permits. Nothing else.

## Prerequisites

- macOS or Linux
- [`uv`](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A TeamViewer **script token** — see below

## Generate a TeamViewer script token

1. Sign in at <https://login.teamviewer.com>.
2. Top-right avatar → **Edit profile** → **Apps & Tokens**.
3. **Create app or token** → choose **Script** (not OAuth app).
4. Tick at minimum:
   - Account → **Read**
   - User management → **View users**
   - Group management → **View groups**
   - Connection reporting → **View connection report entries**
   - Computer & Contacts → **View entries**
   - Service cases → **View** (only if your licence exposes Assist sessions)
5. Save and copy the token. Treat it like a password.

> If a permission is greyed out, your account is company-managed and a Company Admin needs to grant the matching permission on your user. Connection reporting is the one that's most often locked down.

## Configure as an MCP server in Claude Code

Add this to `~/.claude.json` under `mcpServers` (create the key if it doesn't exist):

```json
"teamviewer": {
  "type": "stdio",
  "command": "uvx",
  "args": [
    "--python", "3.12",
    "--with", "httpx",
    "--from", "mcp[cli]>=1.2",
    "python",
    "/absolute/path/to/teamviewer_mcp.py"
  ],
  "env": {
    "TEAMVIEWER_TOKEN": "paste-your-script-token-here"
  }
}
```

Replace `/absolute/path/to/teamviewer_mcp.py` with wherever you cloned this repo. On Linux/macOS without `uv` on the system PATH, use the full path to `uvx` (`~/.local/bin/uvx`).

Restart Claude Code (or run `/mcp` to reconnect). The `teamviewer` server should show **connected** with 7 tools listed.

## Sanity-check it works

In Claude Code, ask:

> Use tv_whoami.

You should see your TeamViewer account email come back. Then:

> Pull the TeamViewer connection report for the last 30 days and summarise total session minutes per user.

Claude will call `tv_connection_report` with the right date range and analyse the results.

## Other MCP clients

The server speaks plain stdio MCP, so anything that supports MCP works — Claude Desktop, Cursor, Continue, custom Agent SDK clients, etc. Point them at `python teamviewer_mcp.py` with `TEAMVIEWER_TOKEN` set in the environment.

## Limitations / things to know

- **`/reports/connections` is capped at 1,000 records per call.** Older records are reachable via the `offset_id` paging parameter (use the last record's id from the previous page).
- **Filters that 403** mean the token is missing that specific permission tick. Re-create the token with the right boxes ticked and replace the env var.
- **Service cases endpoint differs by licence.** Some accounts expose `/servicecases`, others `/sessions`. This server uses `/sessions`. If you get a 404, swap the path in `tv_list_service_cases` and please open a PR with the variant for your licence.
- **No retries, no caching, no rate-limit handling.** This is a thin wrapper. TeamViewer's API is generally well-behaved for human-paced reporting use, but heavy automation should add backoff.

## Local development

```bash
# Install deps in a throwaway venv via uv
uv pip install --system -r requirements.txt   # or use a real venv

# Run directly (talks MCP over stdio — exit with Ctrl+C)
TEAMVIEWER_TOKEN=… python teamviewer_mcp.py
```

To test calls without an MCP client, the easiest thing is `curl`:

```bash
curl -s -H "Authorization: Bearer $TEAMVIEWER_TOKEN" \
     -H "Accept: application/json" \
     https://webapi.teamviewer.com/api/v1/account | jq
```

If that returns your account, the MCP server will too.

## Project structure

```
teamviewer_mcp.py      # The MCP server — ~110 lines, the entire implementation
requirements.txt       # mcp[cli], httpx
README.md
.gitignore
```

## Contributing

PRs welcome — especially for additional read-only endpoints, alternative paths for licence-specific endpoints, or write tools behind an explicit opt-in flag.

## License

MIT — pick a `LICENSE` file when you publish if you want to be explicit.
