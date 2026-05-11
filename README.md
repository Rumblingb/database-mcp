#      1|# Database MCP — Query databases from AI agents

[![smithery badge](https://smithery.ai/badge/vishar-rumbling/database-mcp)](https://smithery.ai/servers/vishar-rumbling/database-mcp)

Query SQLite, PostgreSQL, and MySQL databases directly from any MCP-compatible AI agent.

**$19/month** — Unlimited database queries for your AI agents.
▶ [Subscribe Now](https://buy.stripe.com/dRm6oJ4Hd2Jugek0wz1oI0m)

## Tools

| Tool | Description |
|------|-------------|
| `db_query` | Execute any SQL query |
| `db_list_tables` | List all tables in a database |
| `db_describe_table` | Get table schema information |

## Quick Start

```bash
# SQLite
python3 server.py
# Then configure in Claude: db_query('SELECT * FROM users', 'sqlite', '/path/to/db.sqlite')
```

GitHub: github.com/Rumblingb/database-mcp
