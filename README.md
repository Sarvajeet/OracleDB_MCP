# Oracle Database MCP Server

A custom **Model Context Protocol (MCP)** server that connects AI assistants — Cursor, Claude Desktop, Windsurf, and any MCP-compatible client — to an **Oracle Database**. Built with Python using the [`mcp`](https://pypi.org/project/mcp/) SDK (FastMCP) and [`python-oracledb`](https://pypi.org/project/oracledb/) in thin mode (no Oracle Client installation required).

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Client Configuration](#client-configuration)
- [MCP Tools Reference](#mcp-tools-reference)
- [MCP Resources Reference](#mcp-resources-reference)
- [Usage Examples](#usage-examples)
- [Environment Variables](#environment-variables)
- [Security](#security)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

| Category | Capability |
|----------|-----------|
| **Query** | Execute SELECT statements with bind parameters and configurable row limits |
| **DML** | Execute INSERT / UPDATE / DELETE with auto-commit control |
| **DDL** | Execute CREATE / ALTER / DROP / TRUNCATE statements |
| **PL/SQL** | Run anonymous blocks, stored procedures, and functions with DBMS_OUTPUT capture |
| **Export** | Export query results as CSV or JSON text |
| **Schema** | Browse schemas, list tables, describe columns/types/PKs, list constraints |
| **Safety** | Read-only mode, row limits, error handling, no credential exposure |
| **Transport** | Supports both stdio (local) and SSE (remote/web) transports |

---

## Prerequisites

- **Python** 3.10 or higher
- **Oracle Database** 19c, 21c, or 23ai (on-premises, cloud, or local — e.g. Oracle Free)
- **Network access** to the Oracle listener (default port 1521)

> **Note:** This server uses `python-oracledb` in **thin mode**, so you do **not** need to install Oracle Instant Client or any native Oracle libraries.

---

## Installation

### From source (editable / development)

```bash
git clone <repo-url>
cd OracleDB_MCP
pip install -e .
```

### Using pip directly

```bash
pip install -e C:\AI\OracleDB_MCP
```

This installs the following dependencies automatically:

| Package | Purpose |
|---------|---------|
| `mcp[cli]` >= 1.2.0 | MCP SDK with FastMCP server and CLI support |
| `oracledb` >= 2.0.0 | Oracle Database driver (thin mode) |
| `pydantic-settings` >= 2.0.0 | Typed configuration from environment variables |
| `python-dotenv` >= 1.0.0 | Load `.env` files |

---

## Configuration

Create a `.env` file in the project root (or set environment variables directly):

```env
# Oracle Database Connection
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE=FREEPDB1
ORACLE_USER=system
ORACLE_PASSWORD=your_password_here

# Optional: full DSN override (if set, HOST/PORT/SERVICE are ignored)
# ORACLE_DSN=localhost:1521/FREEPDB1

# Connection pool sizing
ORACLE_MIN_POOL=1
ORACLE_MAX_POOL=5

# Safety settings
ORACLE_READONLY=false      # Set to true to disable DML/DDL/PL/SQL tools
ORACLE_MAX_ROWS=500        # Default row limit for query results

# MCP Server Transport
MCP_TRANSPORT=stdio        # "stdio" or "sse"
MCP_SSE_HOST=0.0.0.0
MCP_SSE_PORT=8000
```

You can also pass connection details via environment variables when launching from an MCP client (see [Client Configuration](#client-configuration)).

---

## Running the Server

### stdio transport (default — for Cursor, Claude Desktop)

```bash
python -m oracle_mcp
```

### SSE transport (for remote / web-based access)

```bash
python -m oracle_mcp --transport sse --port 8000
```

### Using the installed entry point

```bash
oracle-mcp
oracle-mcp --transport sse --port 8000
```

### CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--transport` | `stdio` | Transport type: `stdio` or `sse` |
| `--host` | `0.0.0.0` | Host to bind for SSE transport |
| `--port` | `8000` | Port to listen on for SSE transport |

---

## Client Configuration

### Cursor

Add to your project's `.cursor/mcp.json` or global MCP settings:

```json
{
  "mcpServers": {
    "oracle-db": {
      "command": "python",
      "args": ["-m", "oracle_mcp"],
      "env": {
        "ORACLE_HOST": "localhost",
        "ORACLE_PORT": "1521",
        "ORACLE_SERVICE": "FREEPDB1",
        "ORACLE_USER": "hr",
        "ORACLE_PASSWORD": "your_password"
      }
    }
  }
}
```

### Claude Desktop

Add to `claude_desktop_config.json` (typically at `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "oracle-db": {
      "command": "python",
      "args": ["-m", "oracle_mcp"],
      "env": {
        "ORACLE_HOST": "localhost",
        "ORACLE_PORT": "1521",
        "ORACLE_SERVICE": "FREEPDB1",
        "ORACLE_USER": "hr",
        "ORACLE_PASSWORD": "your_password"
      }
    }
  }
}
```

### SSE Transport (remote server)

If the MCP server is running remotely via SSE:

```json
{
  "mcpServers": {
    "oracle-db": {
      "url": "http://your-server:8000/sse"
    }
  }
}
```

### Read-Only Mode

To restrict the server to SELECT queries and schema exploration only:

```json
{
  "mcpServers": {
    "oracle-db": {
      "command": "python",
      "args": ["-m", "oracle_mcp"],
      "env": {
        "ORACLE_HOST": "localhost",
        "ORACLE_PORT": "1521",
        "ORACLE_SERVICE": "FREEPDB1",
        "ORACLE_USER": "report_user",
        "ORACLE_PASSWORD": "your_password",
        "ORACLE_READONLY": "true"
      }
    }
  }
}
```

---

## MCP Tools Reference

### `execute_query`

Run a SELECT statement and get formatted tabular results.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL SELECT statement |
| `params` | string | No | JSON bind parameters (e.g. `'{"dept_id": 10}'`) |
| `max_rows` | integer | No | Max rows to return (default: 500) |

### `execute_dml`

Run INSERT, UPDATE, or DELETE statements.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | DML statement |
| `params` | string | No | JSON bind parameters |
| `auto_commit` | boolean | No | Auto-commit after execution (default: true) |

> Disabled when `ORACLE_READONLY=true`.

### `execute_ddl`

Run CREATE, ALTER, DROP, or TRUNCATE statements.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | DDL statement |

> Disabled when `ORACLE_READONLY=true`.

### `execute_plsql`

Execute anonymous PL/SQL blocks, stored procedures, or functions. Any output from `DBMS_OUTPUT.PUT_LINE` is captured and returned.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plsql_block` | string | Yes | PL/SQL block (e.g. `BEGIN ... END;`) |
| `params` | string | No | JSON bind parameters |

> Disabled when `ORACLE_READONLY=true`.

### `export_csv`

Run a SELECT query and return the results as CSV text.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL SELECT statement |
| `params` | string | No | JSON bind parameters |
| `max_rows` | integer | No | Max rows to export |

### `export_json`

Run a SELECT query and return the results as a JSON array of objects (keyed by column name).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | Yes | SQL SELECT statement |
| `params` | string | No | JSON bind parameters |
| `max_rows` | integer | No | Max rows to export |

---

## MCP Resources Reference

Resources provide read-only schema exploration through URI-based access:

| URI Pattern | Description |
|-------------|-------------|
| `oracle://schemas` | List all accessible schemas (users) in the database |
| `oracle://schemas/{schema}/tables` | List all tables in a specific schema with row counts |
| `oracle://schemas/{schema}/tables/{table}` | Describe table structure: columns, data types, nullability, primary keys |
| `oracle://schemas/{schema}/tables/{table}/constraints` | List all constraints: primary key, foreign key, unique, check |

> Schema and table names are case-insensitive (auto-uppercased).

---

## Usage Examples

Once configured in your MCP client, you can interact with the Oracle database using natural language. Here are examples of prompts you might use:

**Querying data:**
> "Show me the first 10 rows from the EMPLOYEES table in the HR schema."

**Schema exploration:**
> "What tables exist in the HR schema? Describe the EMPLOYEES table."

**Modifying data:**
> "Insert a new department with ID 999 and name 'AI Research' into the DEPARTMENTS table."

**Running PL/SQL:**
> "Call the calculate_bonus procedure for employee ID 100."

**Exporting data:**
> "Export all employees in department 50 as a CSV."

**DDL operations:**
> "Create a new table called PROJECT_TASKS with columns for id, name, status, and due_date."

---

## Environment Variables

### Oracle Connection

| Variable | Default | Description |
|----------|---------|-------------|
| `ORACLE_HOST` | `localhost` | Oracle Database hostname or IP address |
| `ORACLE_PORT` | `1521` | Oracle listener port |
| `ORACLE_SERVICE` | `FREEPDB1` | Oracle service name |
| `ORACLE_USER` | `system` | Database username |
| `ORACLE_PASSWORD` | *(empty)* | Database password |
| `ORACLE_DSN` | *(none)* | Full DSN string (overrides HOST/PORT/SERVICE if set) |

### Connection Pool

| Variable | Default | Description |
|----------|---------|-------------|
| `ORACLE_MIN_POOL` | `1` | Minimum number of connections in the pool |
| `ORACLE_MAX_POOL` | `5` | Maximum number of connections in the pool |

### Safety

| Variable | Default | Description |
|----------|---------|-------------|
| `ORACLE_READONLY` | `false` | When `true`, disables DML, DDL, and PL/SQL tools |
| `ORACLE_MAX_ROWS` | `500` | Default maximum rows returned by queries |

### MCP Transport

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport type: `stdio` or `sse` |
| `MCP_SSE_HOST` | `0.0.0.0` | Host address for SSE transport |
| `MCP_SSE_PORT` | `8000` | Port number for SSE transport |

---

## Security

This server is designed with safety in mind:

- **Read-only mode:** Set `ORACLE_READONLY=true` to disable all DML, DDL, and PL/SQL tools entirely. Only SELECT queries and schema exploration remain available.
- **Least privilege:** Always use a database user with the minimum privileges required. For read-only use, grant only `SELECT` and `CREATE SESSION`.
- **Row limits:** Queries are capped at `ORACLE_MAX_ROWS` (default 500) to prevent accidentally returning enormous result sets.
- **No credential exposure:** Database credentials are never returned through tools or resources.
- **Error containment:** All SQL execution is wrapped in try/except blocks. Errors are returned as descriptive text messages — raw stack traces are never exposed.
- **AI guardrails:** DML and DDL tool descriptions include WARNING prompts that instruct the AI model to confirm destructive operations with the user before executing.
- **Production safety:** Avoid pointing this server at production databases. Use read-only replicas or test/development environments instead.

---

## Architecture

```
MCP Client (Cursor / Claude Desktop / etc.)
    |
    |  stdio  or  SSE (HTTP)
    v
FastMCP Server  (server.py)
    |
    |--- Tools:   execute_query, execute_dml, execute_ddl,
    |              execute_plsql, export_csv, export_json
    |
    |--- Resources: oracle://schemas/...
    |
    v
Database Layer  (db.py)
    |
    |  async connection pool (oracledb thin mode)
    v
Oracle Database  (19c / 21c / 23ai)
```

---

## Project Structure

```
OracleDB_MCP/
  pyproject.toml              # Package definition, dependencies, entry points
  README.md                   # This file
  .env.example                # Template for environment variables
  src/
    oracle_mcp/
      __init__.py             # Package entry point, exports main()
      __main__.py             # Enables: python -m oracle_mcp
      server.py               # FastMCP server — registers all tools and resources
      config.py               # Pydantic settings loaded from env vars / .env
      db.py                   # Async Oracle connection pool and SQL execution helpers
      tools/
        __init__.py
        query.py              # execute_query — SELECT with formatted table output
        dml.py                # execute_dml — INSERT/UPDATE/DELETE with commit
        ddl.py                # execute_ddl — CREATE/ALTER/DROP/TRUNCATE
        plsql.py              # execute_plsql — PL/SQL blocks with DBMS_OUTPUT
        export.py             # export_csv, export_json
      resources/
        __init__.py
        schema.py             # Schema exploration: schemas, tables, describe, constraints
```

---

## Troubleshooting

### Connection refused / ORA-12541: TNS:no listener

Verify that the Oracle listener is running and accessible:
```bash
tnsping localhost:1521/FREEPDB1
```
Or check via Python:
```bash
python -c "import oracledb; c = oracledb.connect(user='system', password='pass', dsn='localhost:1521/FREEPDB1'); print(c.version)"
```

### ORA-01017: invalid username/password

Double-check `ORACLE_USER` and `ORACLE_PASSWORD` in your `.env` or client config.

### Tools not appearing in Cursor

1. Ensure the server is configured in `.cursor/mcp.json`.
2. Restart Cursor after changing MCP configuration.
3. Check Cursor's MCP logs for startup errors.

### DML / DDL tools returning "read-only mode" error

`ORACLE_READONLY` is set to `true`. Set it to `false` to enable write operations.

### Large result sets are truncated

Increase `ORACLE_MAX_ROWS` or pass a higher `max_rows` parameter to the query tool.

---

## License

This project is provided as-is for development and educational purposes.
