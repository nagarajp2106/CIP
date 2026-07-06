"""
Database Utilities — CRUD operations, pagination, search, filters, and backup.
"""
import sqlite3
import shutil
import os
import datetime
import pandas as pd
from database import get_connection
from config import DATABASE_PATH, DEFAULT_PAGE_SIZE


def get_paginated_data(table: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE,
                       filters: dict = None, search: str = "", search_columns: list = None,
                       order_by: str = None) -> tuple[pd.DataFrame, int]:
    """
    Fetch paginated data from a table with optional filters and search.

    Args:
        table: Table name
        page: Page number (1-indexed)
        page_size: Rows per page
        filters: Dict of {column: value} for exact match filters
        search: Search string to match across search_columns
        search_columns: Columns to search in
        order_by: Column to order by (prefix with - for DESC)

    Returns:
        Tuple of (DataFrame, total_count)
    """
    conn = get_connection()
    conditions = []
    params = []

    # Apply filters
    if filters:
        for col, val in filters.items():
            if val is not None and val != "" and val != "All":
                conditions.append(f"{col} = ?")
                params.append(val)

    # Apply search
    if search and search_columns:
        search_conds = [f"{col} LIKE ?" for col in search_columns]
        conditions.append(f"({' OR '.join(search_conds)})")
        params.extend([f"%{search}%"] * len(search_columns))

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM {table} {where}"
    total = pd.read_sql(count_query, conn, params=params).iloc[0]["total"]

    # Order
    order_clause = ""
    if order_by:
        if order_by.startswith("-"):
            order_clause = f"ORDER BY {order_by[1:]} DESC"
        else:
            order_clause = f"ORDER BY {order_by}"

    # Paginate
    offset = (page - 1) * page_size
    query = f"SELECT * FROM {table} {where} {order_clause} LIMIT ? OFFSET ?"
    params.extend([page_size, offset])

    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df, int(total)


def get_all_data(table: str, filters: dict = None, limit: int = None) -> pd.DataFrame:
    """Fetch all data from a table with optional filters."""
    conn = get_connection()
    conditions = []
    params = []

    if filters:
        for col, val in filters.items():
            if val is not None and val != "" and val != "All":
                conditions.append(f"{col} = ?")
                params.append(val)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit_clause = f"LIMIT {limit}" if limit else ""

    df = pd.read_sql(f"SELECT * FROM {table} {where} {limit_clause}", conn, params=params)
    conn.close()
    return df


def insert_record(table: str, data: dict) -> bool:
    """Insert a single record into a table."""
    conn = get_connection()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    try:
        conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            list(data.values())
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def update_record(table: str, id_column: str, id_value, data: dict) -> bool:
    """Update a record by its ID column."""
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in data)
    values = list(data.values()) + [id_value]
    conn.execute(f"UPDATE {table} SET {set_clause} WHERE {id_column} = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_record(table: str, id_column: str, id_value) -> bool:
    """Delete a record by its ID column."""
    conn = get_connection()
    conn.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (id_value,))
    conn.commit()
    conn.close()
    return True


def get_table_stats(table: str) -> dict:
    """Get basic statistics for a table."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]

    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]

    conn.close()
    return {"row_count": count, "columns": columns, "column_count": len(columns)}


def get_distinct_values(table: str, column: str) -> list:
    """Get distinct values for a column (for filter dropdowns)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column}")
    values = [row[0] for row in cursor.fetchall()]
    conn.close()
    return values


def execute_query(sql: str, params: list = None) -> pd.DataFrame:
    """Execute a parameterized query and return results as DataFrame."""
    conn = get_connection()
    df = pd.read_sql(sql, conn, params=params or [])
    conn.close()
    return df


def backup_database() -> str:
    """
    Create a timestamped backup of the database.

    Returns:
        Path to the backup file.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.path.dirname(DATABASE_PATH), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"banking_backup_{timestamp}.db")
    shutil.copy2(DATABASE_PATH, backup_path)
    return backup_path


def get_column_summary(table: str, column: str) -> dict:
    """Get summary statistics for a numeric column."""
    conn = get_connection()
    query = f"""
        SELECT
            COUNT({column}) as count,
            AVG({column}) as mean,
            MIN({column}) as min,
            MAX({column}) as max,
            SUM({column}) as sum
        FROM {table}
        WHERE {column} IS NOT NULL
    """
    result = pd.read_sql(query, conn).iloc[0].to_dict()
    conn.close()
    return result
