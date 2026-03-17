"""MCP tool: execute_dml — run INSERT/UPDATE/DELETE statements against Oracle Database."""

from __future__ import annotations

from typing import Any

from oracle_mcp import db


async def execute_dml_tool(
    sql: str,
    params: str | None = None,
    auto_commit: bool = True,
) -> str:
    """Execute a DML statement (INSERT, UPDATE, DELETE) against the Oracle database.

    WARNING: This tool modifies data. The AI model should confirm the operation with
    the user before executing destructive statements.

    Args:
        sql: DML statement (INSERT, UPDATE, or DELETE).
        params: Optional JSON string of bind parameters (e.g. '{"name": "John", "id": 1}').
        auto_commit: Whether to commit automatically after execution. Defaults to True.

    Returns:
        A message indicating the number of affected rows, or an error message.
    """
    import json

    try:
        parsed_params: dict[str, Any] | list[Any] | None = None
        if params:
            parsed_params = json.loads(params)

        rowcount = await db.execute_dml(sql, parsed_params, auto_commit)
        commit_msg = " (committed)" if auto_commit else " (not committed — call commit manually)"
        return f"DML executed successfully. {rowcount} row(s) affected{commit_msg}."

    except Exception as e:
        return f"Error executing DML: {type(e).__name__}: {e}"


