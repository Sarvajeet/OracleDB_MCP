"""MCP tool: execute_plsql — run PL/SQL blocks against Oracle Database."""

from __future__ import annotations

from typing import Any

from oracle_mcp import db


async def execute_plsql_tool(
    plsql_block: str,
    params: str | None = None,
) -> str:
    """Execute an anonymous PL/SQL block against the Oracle database.

    Use this for calling stored procedures, functions, or running PL/SQL logic.
    Any output from DBMS_OUTPUT.PUT_LINE will be captured and returned.

    Args:
        plsql_block: The PL/SQL block to execute (e.g. 'BEGIN my_proc(:1); END;' or a full anonymous block).
        params: Optional JSON string of bind parameters as a dict (e.g. '{"p_id": 1}').

    Returns:
        Success message with any DBMS_OUTPUT captured, or an error message.
    """
    import json

    try:
        parsed_params: dict[str, Any] | None = None
        if params:
            parsed_params = json.loads(params)

        result = await db.execute_plsql(plsql_block, parsed_params)
        return result

    except Exception as e:
        return f"Error executing PL/SQL: {type(e).__name__}: {e}"


