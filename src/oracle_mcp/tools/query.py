"""MCP tool: execute_query — run SELECT statements against Oracle Database."""

from __future__ import annotations

from typing import Any

from oracle_mcp import db
from oracle_mcp.config import oracle_settings


def _format_table(columns: list[str], rows: list[list[Any]]) -> str:
    """Format query results as an aligned text table."""
    if not columns:
        return "(no columns returned)"
    if not rows:
        return f"Columns: {', '.join(columns)}\n\n(0 rows)"

    # Convert all values to strings
    str_rows = [[str(v) if v is not None else "NULL" for v in row] for row in rows]

    # Calculate column widths
    widths = [len(c) for c in columns]
    for row in str_rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    # Build header
    header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
    separator = "-+-".join("-" * w for w in widths)

    # Build rows
    lines = [header, separator]
    for row in str_rows:
        lines.append(" | ".join(val.ljust(w) for val, w in zip(row, widths)))

    lines.append(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(lines)


async def execute_query_tool(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query against the Oracle database and return formatted results.

    Args:
        sql: SQL SELECT statement to execute.
        params: Optional JSON string of bind parameters (e.g. '{"dept_id": 10}' or '[10, "Sales"]').
        max_rows: Maximum number of rows to return. Defaults to server configured limit.

    Returns:
        Formatted text table of query results, or an error message.
    """
    import json

    try:
        parsed_params: dict[str, Any] | list[Any] | None = None
        if params:
            parsed_params = json.loads(params)

        limit = max_rows if max_rows is not None else oracle_settings.max_rows
        columns, rows = await db.execute_query(sql, parsed_params, limit)
        return _format_table(columns, rows)

    except Exception as e:
        return f"Error executing query: {type(e).__name__}: {e}"


