"""MCP resources: schema exploration for Oracle Database."""

from __future__ import annotations

from oracle_mcp import db


async def list_schemas() -> str:
    """List all accessible schemas in the Oracle database.

    Returns:
        A newline-separated list of schema names.
    """
    try:
        columns, rows = await db.execute_query(
            "SELECT username FROM all_users ORDER BY username",
            max_rows=2000,
        )
        if not rows:
            return "(no schemas found)"
        return "\n".join(row[0] for row in rows)
    except Exception as e:
        return f"Error listing schemas: {type(e).__name__}: {e}"


async def list_tables(schema: str) -> str:
    """List all tables in the specified schema.

    Args:
        schema: The schema/owner name (case-insensitive, will be uppercased).

    Returns:
        A formatted list of tables with row counts.
    """
    try:
        schema_upper = schema.upper()
        columns, rows = await db.execute_query(
            """
            SELECT table_name, num_rows, last_analyzed
            FROM all_tables
            WHERE owner = :schema
            ORDER BY table_name
            """,
            {"schema": schema_upper},
            max_rows=2000,
        )
        if not rows:
            return f"(no tables found in schema '{schema_upper}')"

        lines = [f"Tables in schema {schema_upper}:", ""]
        for row in rows:
            name = row[0]
            num_rows = row[1] if row[1] is not None else "?"
            analyzed = row[2] if row[2] is not None else "never"
            lines.append(f"  {name}  (rows: {num_rows}, last analyzed: {analyzed})")

        lines.append(f"\nTotal: {len(rows)} table(s)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing tables: {type(e).__name__}: {e}"


async def describe_table(schema: str, table: str) -> str:
    """Describe a table: columns, data types, nullability, and primary key info.

    Args:
        schema: The schema/owner name.
        table: The table name.

    Returns:
        A formatted table description including columns, types, and constraints.
    """
    try:
        schema_upper = schema.upper()
        table_upper = table.upper()

        # Get columns
        col_columns, col_rows = await db.execute_query(
            """
            SELECT column_name, data_type, data_length, data_precision, data_scale,
                   nullable, data_default, column_id
            FROM all_tab_columns
            WHERE owner = :schema AND table_name = :table
            ORDER BY column_id
            """,
            {"schema": schema_upper, "table": table_upper},
            max_rows=1000,
        )

        if not col_rows:
            return f"Table '{schema_upper}.{table_upper}' not found or has no columns."

        # Get primary key columns
        _, pk_rows = await db.execute_query(
            """
            SELECT cols.column_name
            FROM all_constraints cons
            JOIN all_cons_columns cols
              ON cons.constraint_name = cols.constraint_name
             AND cons.owner = cols.owner
            WHERE cons.owner = :schema
              AND cons.table_name = :table
              AND cons.constraint_type = 'P'
            ORDER BY cols.position
            """,
            {"schema": schema_upper, "table": table_upper},
            max_rows=100,
        )
        pk_columns = {row[0] for row in pk_rows} if pk_rows else set()

        # Format output
        lines = [f"Table: {schema_upper}.{table_upper}", ""]
        lines.append(f"{'#':<4} {'Column':<30} {'Type':<25} {'Null?':<6} {'PK':<4} {'Default'}")
        lines.append("-" * 100)

        for row in col_rows:
            col_name = row[0]
            data_type = row[1]
            data_length = row[2]
            precision = row[3]
            scale = row[4]
            nullable = row[5]
            default = str(row[6]).strip() if row[6] is not None else ""
            col_id = row[7]

            # Build type string
            if precision is not None:
                if scale is not None and scale > 0:
                    type_str = f"{data_type}({precision},{scale})"
                else:
                    type_str = f"{data_type}({precision})"
            elif data_type in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR", "RAW"):
                type_str = f"{data_type}({data_length})"
            else:
                type_str = data_type

            pk_marker = "PK" if col_name in pk_columns else ""
            null_str = "Y" if nullable == "Y" else "N"

            lines.append(
                f"{col_id:<4} {col_name:<30} {type_str:<25} {null_str:<6} {pk_marker:<4} {default}"
            )

        lines.append(f"\n{len(col_rows)} column(s)")
        if pk_columns:
            lines.append(f"Primary key: ({', '.join(sorted(pk_columns))})")

        return "\n".join(lines)
    except Exception as e:
        return f"Error describing table: {type(e).__name__}: {e}"


async def list_constraints(schema: str, table: str) -> str:
    """List all constraints for a table (PK, FK, unique, check).

    Args:
        schema: The schema/owner name.
        table: The table name.

    Returns:
        A formatted list of constraints.
    """
    try:
        schema_upper = schema.upper()
        table_upper = table.upper()

        _, rows = await db.execute_query(
            """
            SELECT c.constraint_name,
                   c.constraint_type,
                   c.status,
                   c.search_condition,
                   c.r_constraint_name,
                   LISTAGG(cc.column_name, ', ') WITHIN GROUP (ORDER BY cc.position) AS columns
            FROM all_constraints c
            LEFT JOIN all_cons_columns cc
              ON c.constraint_name = cc.constraint_name
             AND c.owner = cc.owner
            WHERE c.owner = :schema
              AND c.table_name = :table
            GROUP BY c.constraint_name, c.constraint_type, c.status,
                     c.search_condition, c.r_constraint_name
            ORDER BY c.constraint_type, c.constraint_name
            """,
            {"schema": schema_upper, "table": table_upper},
            max_rows=500,
        )

        if not rows:
            return f"No constraints found for '{schema_upper}.{table_upper}'."

        type_map = {
            "P": "PRIMARY KEY",
            "R": "FOREIGN KEY",
            "U": "UNIQUE",
            "C": "CHECK",
        }

        lines = [f"Constraints for {schema_upper}.{table_upper}:", ""]
        for row in rows:
            name = row[0]
            ctype = type_map.get(row[1], row[1])
            status = row[2]
            search_cond = row[3]
            ref_constraint = row[4]
            columns = row[5]

            line = f"  {name} ({ctype}) on ({columns}) [{status}]"
            if ref_constraint:
                line += f" references {ref_constraint}"
            if search_cond and row[1] == "C":
                line += f" — {search_cond}"
            lines.append(line)

        lines.append(f"\nTotal: {len(rows)} constraint(s)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing constraints: {type(e).__name__}: {e}"


