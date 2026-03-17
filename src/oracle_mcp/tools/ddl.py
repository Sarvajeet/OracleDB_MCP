"""MCP tool: execute_ddl — run CREATE/ALTER/DROP statements against Oracle Database."""

from __future__ import annotations

from oracle_mcp import db


async def execute_ddl_tool(sql: str) -> str:
    """Execute a DDL statement (CREATE, ALTER, DROP, TRUNCATE, etc.) against the Oracle database.

    WARNING: This tool modifies database schema. The AI model should confirm the operation
    with the user before executing, especially DROP statements.

    Args:
        sql: DDL statement to execute (CREATE TABLE, ALTER TABLE, DROP TABLE, etc.).

    Returns:
        A success message or an error message.
    """
    try:
        result = await db.execute_ddl(sql)
        return result
    except Exception as e:
        return f"Error executing DDL: {type(e).__name__}: {e}"


