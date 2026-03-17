"""Oracle Database connection pool and query execution helpers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import oracledb

from oracle_mcp.config import oracle_settings

logger = logging.getLogger("oracle_mcp.db")

# Module-level pool reference
_pool: oracledb.AsyncConnectionPool | None = None


async def init_pool() -> oracledb.AsyncConnectionPool:
    """Create and return the async connection pool (idempotent)."""
    global _pool
    if _pool is not None:
        return _pool

    logger.info(
        "Creating Oracle connection pool: %s@%s (pool %d–%d)",
        oracle_settings.user,
        oracle_settings.connect_dsn,
        oracle_settings.min_pool,
        oracle_settings.max_pool,
    )

    _pool = oracledb.create_pool_async(
        user=oracle_settings.user,
        password=oracle_settings.password,
        dsn=oracle_settings.connect_dsn,
        min=oracle_settings.min_pool,
        max=oracle_settings.max_pool,
    )
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close(force=True)
        _pool = None
        logger.info("Oracle connection pool closed.")


@asynccontextmanager
async def get_connection():
    """Acquire a connection from the pool (async context manager)."""
    pool = await init_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


async def execute_query(
    sql: str,
    params: dict[str, Any] | list[Any] | None = None,
    max_rows: int | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Execute a SELECT query and return (column_names, rows).

    Args:
        sql: The SQL SELECT statement.
        params: Optional bind parameters (dict for named, list for positional).
        max_rows: Maximum number of rows to return. Defaults to config value.

    Returns:
        A tuple of (column_names, rows) where rows is a list of lists.
    """
    if max_rows is None:
        max_rows = oracle_settings.max_rows

    async with get_connection() as conn:
        with conn.cursor() as cursor:
            if params:
                await cursor.execute(sql, params)
            else:
                await cursor.execute(sql)

            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = await cursor.fetchmany(max_rows)
            return columns, [list(row) for row in rows]


async def execute_dml(
    sql: str,
    params: dict[str, Any] | list[Any] | None = None,
    auto_commit: bool = True,
) -> int:
    """Execute a DML statement (INSERT/UPDATE/DELETE) and return rowcount.

    Args:
        sql: The DML statement.
        params: Optional bind parameters.
        auto_commit: Whether to commit automatically. Defaults to True.

    Returns:
        Number of affected rows.
    """
    async with get_connection() as conn:
        with conn.cursor() as cursor:
            if params:
                await cursor.execute(sql, params)
            else:
                await cursor.execute(sql)

            rowcount = cursor.rowcount

            if auto_commit:
                await conn.commit()

            return rowcount


async def execute_ddl(sql: str) -> str:
    """Execute a DDL statement (CREATE/ALTER/DROP).

    Args:
        sql: The DDL statement.

    Returns:
        Success message string.
    """
    async with get_connection() as conn:
        with conn.cursor() as cursor:
            await cursor.execute(sql)
            return "DDL executed successfully."


async def execute_plsql(
    plsql_block: str,
    params: dict[str, Any] | None = None,
) -> str:
    """Execute an anonymous PL/SQL block.

    Args:
        plsql_block: The PL/SQL block (BEGIN ... END;).
        params: Optional bind parameters (dict for named binds).

    Returns:
        Success message, or output if DBMS_OUTPUT was enabled.
    """
    async with get_connection() as conn:
        with conn.cursor() as cursor:
            # Enable DBMS_OUTPUT to capture any printed output
            await cursor.callproc("dbms_output.enable")

            if params:
                await cursor.execute(plsql_block, params)
            else:
                await cursor.execute(plsql_block)

            await conn.commit()

            # Retrieve DBMS_OUTPUT lines
            lines: list[str] = []
            status_var = cursor.var(int)
            line_var = cursor.var(str)

            while True:
                await cursor.callproc(
                    "dbms_output.get_line", [line_var, status_var]
                )
                if status_var.getvalue() != 0:
                    break
                lines.append(line_var.getvalue() or "")

            if lines:
                return "PL/SQL executed successfully.\n\nDBMS_OUTPUT:\n" + "\n".join(lines)
            return "PL/SQL executed successfully."


