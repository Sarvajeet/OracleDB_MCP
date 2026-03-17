"""Oracle MCP Server — main entry point.

Creates a FastMCP server and registers all tools and resources for
Oracle Database interaction.
"""

from __future__ import annotations

import argparse
import logging
import sys

from mcp.server.fastmcp import FastMCP

from oracle_mcp.config import oracle_settings, server_settings

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("oracle_mcp")

# ── Create the MCP server ──────────────────────────────────────
mcp = FastMCP(
    "Oracle Database MCP Server",
    description=(
        "MCP server for Oracle Database. Provides tools for SQL queries, "
        "DML, DDL, PL/SQL execution, and data export, along with schema "
        "exploration resources."
    ),
)

# ── Register Tools ─────────────────────────────────────────────

# Import tool implementations
from oracle_mcp.tools.query import execute_query_tool  # noqa: E402
from oracle_mcp.tools.dml import execute_dml_tool  # noqa: E402
from oracle_mcp.tools.ddl import execute_ddl_tool  # noqa: E402
from oracle_mcp.tools.plsql import execute_plsql_tool  # noqa: E402
from oracle_mcp.tools.export import export_csv_tool, export_json_tool  # noqa: E402

# Import resource implementations
from oracle_mcp.resources.schema import (  # noqa: E402
    list_schemas,
    list_tables,
    describe_table,
    list_constraints,
)


# ── Tools ──────────────────────────────────────────────────────

@mcp.tool()
async def execute_query(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query against Oracle and return formatted results.

    Args:
        sql: SQL SELECT statement to execute.
        params: Optional JSON string of bind parameters (e.g. '{"dept_id": 10}').
        max_rows: Maximum number of rows to return.
    """
    return await execute_query_tool(sql, params, max_rows)


@mcp.tool()
async def execute_dml(
    sql: str,
    params: str | None = None,
    auto_commit: bool = True,
) -> str:
    """Execute a DML statement (INSERT, UPDATE, DELETE) against Oracle.

    WARNING: This modifies data. Confirm with the user before executing.

    Args:
        sql: DML statement to execute.
        params: Optional JSON string of bind parameters.
        auto_commit: Whether to commit after execution. Defaults to True.
    """
    if oracle_settings.readonly:
        return "Error: DML execution is disabled. Server is running in read-only mode."
    return await execute_dml_tool(sql, params, auto_commit)


@mcp.tool()
async def execute_ddl(sql: str) -> str:
    """Execute a DDL statement (CREATE, ALTER, DROP, TRUNCATE) against Oracle.

    WARNING: This modifies database schema. Confirm with the user before executing,
    especially for DROP operations.

    Args:
        sql: DDL statement to execute.
    """
    if oracle_settings.readonly:
        return "Error: DDL execution is disabled. Server is running in read-only mode."
    return await execute_ddl_tool(sql)


@mcp.tool()
async def execute_plsql(
    plsql_block: str,
    params: str | None = None,
) -> str:
    """Execute a PL/SQL block against Oracle. Captures DBMS_OUTPUT.

    Use this for stored procedures, functions, or anonymous PL/SQL blocks.

    Args:
        plsql_block: PL/SQL block (e.g. 'BEGIN my_proc(:id); END;').
        params: Optional JSON string of bind parameters.
    """
    if oracle_settings.readonly:
        return "Error: PL/SQL execution is disabled. Server is running in read-only mode."
    return await execute_plsql_tool(plsql_block, params)


@mcp.tool()
async def export_csv(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query and return results as CSV text.

    Args:
        sql: SQL SELECT statement.
        params: Optional JSON string of bind parameters.
        max_rows: Maximum rows to export.
    """
    return await export_csv_tool(sql, params, max_rows)


@mcp.tool()
async def export_json(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query and return results as JSON (array of objects).

    Args:
        sql: SQL SELECT statement.
        params: Optional JSON string of bind parameters.
        max_rows: Maximum rows to export.
    """
    return await export_json_tool(sql, params, max_rows)


# ── Resources ──────────────────────────────────────────────────

@mcp.resource("oracle://schemas")
async def resource_list_schemas() -> str:
    """List all accessible schemas in the Oracle database."""
    return await list_schemas()


@mcp.resource("oracle://schemas/{schema}/tables")
async def resource_list_tables(schema: str) -> str:
    """List all tables in the specified Oracle schema."""
    return await list_tables(schema)


@mcp.resource("oracle://schemas/{schema}/tables/{table}")
async def resource_describe_table(schema: str, table: str) -> str:
    """Describe the structure of a specific Oracle table (columns, types, PKs)."""
    return await describe_table(schema, table)


@mcp.resource("oracle://schemas/{schema}/tables/{table}/constraints")
async def resource_list_constraints(schema: str, table: str) -> str:
    """List all constraints for a specific Oracle table."""
    return await list_constraints(schema, table)


# ── Main entry point ───────────────────────────────────────────

def main():
    """Run the Oracle MCP server."""
    parser = argparse.ArgumentParser(description="Oracle Database MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=server_settings.transport,
        help="MCP transport type (default: %(default)s)",
    )
    parser.add_argument(
        "--host",
        default=server_settings.sse_host,
        help="SSE host to bind to (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=server_settings.sse_port,
        help="SSE port to listen on (default: %(default)s)",
    )
    args = parser.parse_args()

    logger.info("Starting Oracle MCP Server (transport=%s)", args.transport)
    logger.info(
        "Oracle connection: %s@%s (readonly=%s)",
        oracle_settings.user,
        oracle_settings.connect_dsn,
        oracle_settings.readonly,
    )

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host=args.host, port=args.port)


