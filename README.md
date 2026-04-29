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

Plug this server into Claude Code (or any MCP-compatible client) to pull live reports, query user directories, and audit device states from your TeamViewer account using plain English.

## Features

This server exposes seven core tools. All tools are strictly **read-only** and act as secure wrappers around your TeamViewer token, guaranteeing that AI agents cannot execute destructive actions (like deleting users or terminating sessions).

| MCP Tool | TeamViewer Endpoint | Description |
|---|---|---|
| `tv_whoami` | `GET /account` | Sanity check. Confirms your token works and returns your account, email, company, and license level. |
| `tv_connection_report` | `GET /reports/connections` | The main reporting endpoint. Supports filtering by date (`from_date`, `to_date`), `username`, and handles pagination via `offset_id`. |
| `tv_list_users` | `GET /users` | Retrieves company users. Returned fields depend on your specific license and token scope. |
| `tv_list_devices` | `GET /devices` | Lists managed devices, including aliases, online states, groups, and TeamViewer IDs. |
| `tv_list_groups` | `GET /groups` | Lists all device groups available to the authenticated account. |
| `tv_list_contacts` | `GET /contacts` | Retrieves entries from your Computers & Contacts list. |
| `tv_list_service_cases` | `GET /sessions` | Lists active Assist service cases and remote support sessions. |

## Prerequisites

- macOS or Linux
- [`uv`](https://docs.astral.sh/uv/) installed on your system (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- A TeamViewer **script token** (instructions below)

## Generating a Script Token

1. Sign in at the [TeamViewer Management Console](https://login.teamviewer.com).
2. Click your top-right avatar → **Edit profile** → **Apps & Tokens**.
3. Click **Create app or token** and select **Script** (do not select OAuth app).
4. Tick the following minimum read permissions:
   - Account → **Read**
   - User management → **View users**
   - Group management → **View groups**
   - Connection reporting → **View connection report entries**
   - Computer & Contacts → **View entries**
   - Service cases → **View** *(only if your license exposes Assist sessions)*
5. Save and copy the token immediately. **Treat this token like a password.**

> [!NOTE]
> If a permission is greyed out, your account is company-managed. A Company Admin will need to grant the matching permission to your user profile. Connection reporting is typically the most restricted permission.

## Setup in Claude Code

Add the following configuration to your `~/.claude.json` under the `mcpServers` object (create the object if it doesn't exist):

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

*Note: Replace `/absolute/path/to/teamviewer_mcp.py` with the actual path where you cloned this repository. If `uvx` isn't on your system path, provide the full absolute path to the executable (e.g., `~/.local/bin/uvx`).*

Restart Claude Code (or run `/mcp` to reconnect). The `teamviewer` server should now show as **connected** with 7 tools available.

## Usage Example

Once connected, you can interact naturally with your TeamViewer environment.

**1. Verify your connection:**
> "Use tv_whoami to verify my connection."

**2. Generate a custom report:**
> "Pull the TeamViewer connection report for the last 30 days and summarize the total session minutes per user in a markdown table."

Claude will automatically call `tv_connection_report` with the correct ISO-8601 timestamps, paginate if necessary, and analyze the returned data.

## Limitations & Best Practices

- **Pagination:** The `/reports/connections` endpoint is capped at 1,000 records per API call. Older records are reachable via the `offset_id` paging parameter (the LLM handles this by passing the ID of the last record).
- **Permission Errors (403 Forbidden):** If an endpoint returns a 403, your token lacks the specific permission tick for that endpoint. You will need to recreate the token with the correct scopes.
- **License Dependencies:** Some TeamViewer accounts expose service cases at `/servicecases` instead of `/sessions`. This server defaults to `/sessions`. If you encounter a 404 error, you may need to swap the endpoint path in `tv_list_service_cases`.
- **Rate Limiting:** This server acts as a thin, direct wrapper. There are no built-in retries, caching layers, or rate-limit delays. It is highly optimized for human-paced AI workflows, but heavy automation scripts may require explicit backoff logic.

## Local Development

To test the server locally or contribute:

```bash
# Install dependencies in a temporary virtual environment using uv
uv pip install --system -r requirements.txt

# Run directly (the server communicates via stdio — exit with Ctrl+C)
TEAMVIEWER_TOKEN=your_token_here python teamviewer_mcp.py
```

To verify your token is working independently of the MCP wrapper, test it directly with `curl`:

```bash
curl -s -H "Authorization: Bearer $TEAMVIEWER_TOKEN" \
     -H "Accept: application/json" \
     https://webapi.teamviewer.com/api/v1/account
```

## Contributing

Pull Requests are highly encouraged! We especially welcome:
- Additional read-only endpoints.
- Environment variable toggles for alternative license paths (e.g., `/servicecases`).
- Destructive/write tools placed behind explicit, default-off feature flags.

## License

This project is licensed under the [MIT License](LICENSE).
