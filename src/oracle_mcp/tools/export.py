"""MCP tools: export_csv and export_json — export query results in structured formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from oracle_mcp import db
from oracle_mcp.config import oracle_settings


async def export_csv_tool(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query and return results as CSV text.

    Args:
        sql: SQL SELECT statement to execute.
        params: Optional JSON string of bind parameters.
        max_rows: Maximum number of rows to export. Defaults to server configured limit.

    Returns:
        CSV-formatted string of query results, or an error message.
    """
    try:
        parsed_params: dict[str, Any] | list[Any] | None = None
        if params:
            parsed_params = json.loads(params)

        limit = max_rows if max_rows is not None else oracle_settings.max_rows
        columns, rows = await db.execute_query(sql, parsed_params, limit)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)

        return output.getvalue()

    except Exception as e:
        return f"Error exporting CSV: {type(e).__name__}: {e}"


async def export_json_tool(
    sql: str,
    params: str | None = None,
    max_rows: int | None = None,
) -> str:
    """Execute a SQL SELECT query and return results as JSON text.

    Each row is a JSON object keyed by column name.

    Args:
        sql: SQL SELECT statement to execute.
        params: Optional JSON string of bind parameters.
        max_rows: Maximum number of rows to export. Defaults to server configured limit.

    Returns:
        JSON-formatted string of query results (array of objects), or an error message.
    """
    try:
        parsed_params: dict[str, Any] | list[Any] | None = None
        if params:
            parsed_params = json.loads(params)

        limit = max_rows if max_rows is not None else oracle_settings.max_rows
        columns, rows = await db.execute_query(sql, parsed_params, limit)

        result = []
        for row in rows:
            obj = {}
            for col, val in zip(columns, row):
                # Convert non-serializable types to string
                if isinstance(val, (bytes, bytearray)):
                    obj[col] = val.hex()
                else:
                    try:
                        json.dumps(val)
                        obj[col] = val
                    except (TypeError, ValueError):
                        obj[col] = str(val)
            result.append(obj)

        return json.dumps(result, indent=2, default=str)

    except Exception as e:
        return f"Error exporting JSON: {type(e).__name__}: {e}"


