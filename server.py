#!/usr/bin/env python3
"""Database MCP — Query SQLite, PostgreSQL, MySQL, and more from AI agents."""

import json, sqlite3, os, re
from mcp.server import Server, stdio_server

server = Server("database-mcp")

def _get_sqlite_connection(db_path):
    """Get SQLite connection from path."""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    return sqlite3.connect(db_path)

def _get_pg_connection(conn_string):
    """Get PostgreSQL connection from connection string."""
    try:
        import psycopg2
        return psycopg2.connect(conn_string)
    except ImportError:
        raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")

def _get_mysql_connection(conn_string):
    """Get MySQL connection from connection string."""
    try:
        import pymysql
        # Parse connection string: mysql://user:pass@host:port/db
        match = re.match(r'mysql://([^:]+):([^@]+)@([^:]+):?(\d+)?/(.+)', conn_string)
        if match:
            return pymysql.connect(
                host=match.group(3), user=match.group(1), password=match.group(2),
                database=match.group(5), port=int(match.group(4) or 3306)
            )
        raise ValueError(f"Invalid MySQL connection string: {conn_string}")
    except ImportError:
        raise ImportError("pymysql not installed. Install with: pip install pymysql")

def _connect(db_type, connection):
    """Connect to database based on type."""
    if db_type == "sqlite":
        return _get_sqlite_connection(connection)
    elif db_type == "postgresql":
        return _get_pg_connection(connection)
    elif db_type == "mysql":
        return _get_mysql_connection(connection)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def _execute(conn, query, params=None):
    """Execute query and return results."""
    cur = conn.cursor()
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)
    
    if query.strip().upper().startswith(("SELECT", "WITH", "EXPLAIN", "DESCRIBE", "SHOW", "PRAGMA")):
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchmany(100)
        return {"columns": columns, "rows": [list(r) for r in rows], "row_count": len(rows)}
    else:
        conn.commit()
        return {"affected_rows": cur.rowcount, "last_insert_id": cur.lastrowid}

@server.tool(
    name="db_query",
    description="Execute a SQL query against a database. Supports SQLite, PostgreSQL, MySQL.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "SQL query to execute"},
            "db_type": {"type": "string", "enum": ["sqlite", "postgresql", "mysql"], "description": "Database type", "default": "sqlite"},
            "connection": {"type": "string", "description": "For SQLite: path to .db file. For PostgreSQL/MySQL: connection string (postgresql://user:pass@host/db)"},
            "params": {"type": "array", "description": "Optional query parameters", "items": {"type": "string"}}
        },
        "required": ["query", "connection"]
    }
)
async def db_query(query: str, db_type: str = "sqlite", connection: str = "", params: list = None) -> str:
    try:
        # Support env var shortcuts
        if connection.startswith("env:"):
            env_var = connection[4:]
            connection = os.environ.get(env_var, "")
            if not connection:
                return json.dumps({"error": f"Environment variable {env_var} not set", "isError": True}, indent=2)
        
        conn = _connect(db_type, connection)
        result = _execute(conn, query, params)
        conn.close()
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="db_list_tables",
    description="List all tables in a database.",
    input_schema={
        "type": "object",
        "properties": {
            "db_type": {"type": "string", "enum": ["sqlite", "postgresql", "mysql"], "default": "sqlite"},
            "connection": {"type": "string", "description": "DB path or connection string"}
        },
        "required": ["connection"]
    }
)
async def db_list_tables(db_type: str = "sqlite", connection: str = "") -> str:
    try:
        conn = _connect(db_type, connection)
        if db_type == "sqlite":
            result = _execute(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        elif db_type == "postgresql":
            result = _execute(conn, "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        else:  # mysql
            db_name = conn.db if hasattr(conn, 'db') else None
            if db_name:
                result = _execute(conn, f"SHOW TABLES FROM `{db_name}`")
            else:
                result = _execute(conn, "SHOW TABLES")
        conn.close()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="db_describe_table",
    description="Get schema information for a table.",
    input_schema={
        "type": "object",
        "properties": {
            "table_name": {"type": "string", "description": "Table name"},
            "db_type": {"type": "string", "enum": ["sqlite", "postgresql", "mysql"], "default": "sqlite"},
            "connection": {"type": "string", "description": "DB path or connection string"}
        },
        "required": ["table_name", "connection"]
    }
)
async def db_describe_table(table_name: str, db_type: str = "sqlite", connection: str = "") -> str:
    try:
        conn = _connect(db_type, connection)
        if db_type == "sqlite":
            result = _execute(conn, f"PRAGMA table_info(\"{table_name}\")")
        elif db_type == "postgresql":
            result = _execute(conn, f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name='{table_name}' ORDER BY ordinal_position")
        else:
            result = _execute(conn, f"DESCRIBE `{table_name}`")
        conn.close()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

def main():
    import anyio
    async def run():
        async with stdio_server() as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
    anyio.run(run)

if __name__ == "__main__":
    main()
