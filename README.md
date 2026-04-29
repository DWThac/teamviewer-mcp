# 📡 TeamViewer MCP Server

> A standalone test project creating a read-only Model Context Protocol server for the TeamViewer Web API.

![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

---

## Why this exists

This is an unofficial, standalone test project created solely for personal experimentation. It's a minimal read-only wrapper around the TeamViewer Web API, designed to be plugged into Claude Code (or any MCP client) to pull live reports from a TeamViewer account using plain English.

*Note: This project is not affiliated with, endorsed by, or supported by TeamViewer. It is a personal test, use it at your own risk.*

---

## Features

- ✅ Seven strictly read-only tools ensuring no destructive actions can be taken by an AI agent.
- ✅ Pulls connection reports with date filtering and pagination handling.
- ✅ Retrieves user directories, managed devices, and groups based on your token scope.
- ✅ Fetches Computers & Contacts entries and active Assist service cases.
- ✅ Graceful error handling that strictly prevents sensitive data leakage on failed API calls.

---

## Supported Tools

| MCP Tool | TeamViewer Endpoint | Purpose |
|---|---|---|
| `tv_whoami` | `GET /account` | Sanity check — confirms your token works, returns account/email/company/license. |
| `tv_connection_report` | `GET /reports/connections` | The main reporting endpoint. Optional `from_date`, `to_date`, `username`, `offset_id` (paging). |
| `tv_list_users` | `GET /users` | Company users. Returned fields depend on licence and token scope. |
| `tv_list_devices` | `GET /devices` | Managed devices (alias, online state, group, TeamViewer ID). |
| `tv_list_groups` | `GET /groups` | Groups available to this account. |
| `tv_list_contacts` | `GET /contacts` | Computers & Contacts entries. |
| `tv_list_service_cases` | `GET /sessions` | Assist service cases / sessions. |

---

## Setup

### 1. Install dependencies

Ensure you have [`uv`](https://docs.astral.sh/uv/) installed:

```bash
uv pip install --system -r requirements.txt
```

### 2. Generate a TeamViewer script token

1. Sign in at [login.teamviewer.com](https://login.teamviewer.com).
2. Go to **Edit profile** → **Apps & Tokens**.
3. Click **Create app or token** → choose **Script** (not OAuth app).
4. Tick at minimum:
   - Account → **Read**
   - User management → **View users**
   - Group management → **View groups**
   - Connection reporting → **View connection report entries**
   - Computer & Contacts → **View entries**
   - Service cases → **View**
5. Save and copy the token. 

*(If a permission is greyed out, your account is company-managed and a Company Admin needs to grant the matching permission on your user).*

### 3. Configure as an MCP server

Add this to `~/.claude.json` under `mcpServers`:

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

Restart Claude Code. The `teamviewer` server should show as connected.

---

## Usage

Test it out in Claude Code:

> "Use tv_whoami to verify my connection."

> "Pull the TeamViewer connection report for the last 30 days and summarize the total session minutes per user."

---

## Limitations

- **1,000 records limit:** `/reports/connections` is capped per call. The LLM handles older records by passing `offset_id`.
- **403 Errors:** Means the token is missing a permission.
- **Service cases endpoint:** Some accounts expose `/servicecases` instead of `/sessions`. This defaults to `/sessions`.
- **No rate-limit handling:** This is a thin wrapper built for human-paced AI workflows.

---

## Project files

| File | Purpose |
|---|---|
| `teamviewer_mcp.py` | The MCP server — ~240 lines, the entire implementation |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Standard python ignores |
| `LICENSE` | MIT License |

---

## License

MIT — do whatever you like with it.
