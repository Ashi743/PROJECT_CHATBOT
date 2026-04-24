from langchain_core.tools import tool
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import json

DB_DIR = Path(__file__).parent.parent / "data" / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "analytics.db"

def get_connection(db_name: str = "analytics"):
    """Get SQLite database connection

    Args:
        db_name: Database name without .db extension. Defaults to "analytics" for backward compatibility
    """
    if db_name == "analytics":
        db_path = DB_PATH
    else:
        db_path = DB_DIR / f"{db_name}.db"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _validate_table_name(conn, table_name: str) -> bool:
    """Whitelist table name against sqlite_master to prevent SQL injection"""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cur.fetchone() is not None

def _initialize_sample_database():
    """Create sample database if it doesn't exist"""
    if DB_PATH.exists():
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Create schema
    cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP,
        country TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT,
        price REAL,
        stock INTEGER,
        created_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER,
        total_price REAL,
        order_date TIMESTAMP,
        status TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)

    # Load sample data from file
    sql_file = Path(__file__).parent.parent / "data" / "sample_init.sql"
    if sql_file.exists():
        sql_content = sql_file.read_text(encoding="utf-8")
        cursor.executescript(sql_content)

    conn.commit()
    conn.close()

_initialize_sample_database()

@tool
def analyze_sql(query_type: str, table_name: str = "", query: str = "", params: str = "", db_name: str = "analytics") -> str:
    """
    Analyze SQL database using SQLite. The LLM uses this to query and manage data.

    Args:
        query_type: Type of operation. Valid options:
            - 'select' → Execute SELECT query (param: SQL SELECT statement)
            - 'insert' → Insert rows (param: "col1,col2,col3;val1,val2,val3")
            - 'update' → Update rows (param: "col=val,col2=val2;WHERE condition")
            - 'delete' → Delete rows (param: "WHERE condition")
            - 'describe' → Show table schema (param: table_name)
            - 'list_tables' → List all tables in database
            - 'count' → Count rows in table (param: table_name)
            - 'sample' → Show sample rows (param: "table_name,N")
            - 'list_databases' → List all uploaded databases
            - 'get_schema' → Get full schema for a database (param: db_name)
        db_name: Name of database to query (default: "analytics"). Use for uploaded SQL files.
        table_name: Name of table
        query: SQL query string
        params: Additional parameters depending on query_type

    Returns:
        Formatted string result of the query

    Examples:
        - analyze_sql(query_type='select', db_name='insurance', query='SELECT * FROM users')
        - analyze_sql(query_type='list_databases')
        - analyze_sql(query_type='get_schema', db_name='insurance')
    """
    try:
        conn = get_connection(db_name)
        cursor = conn.cursor()

        if query_type == 'select':
            if not query:
                return "[ERROR] select requires SQL query"
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return f"No results found for query"
            df = pd.DataFrame([dict(row) for row in rows])
            return f"Query Results:\n\n{df.to_string()}"

        elif query_type == 'describe':
            if not table_name:
                return "[ERROR] describe requires table_name"
            if not _validate_table_name(conn, table_name):
                return f"[ERROR] Unknown table: {table_name}"
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            if not columns:
                return f"[ERROR] Table '{table_name}' not found"
            info_str = f"Table: {table_name}\n\nColumns:\n"
            for col in columns:
                cid, name, col_type, notnull, dflt_value, pk = col
                nullable = "NOT NULL" if notnull else "nullable"
                primary = " PRIMARY KEY" if pk else ""
                info_str += f"  {name}: {col_type} ({nullable}){primary}\n"
            return info_str

        elif query_type == 'list_tables':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            if not tables:
                return "No tables found in database"
            table_list = "\n".join([f"  - {t[0]}" for t in tables])
            return f"Tables in database:\n{table_list}"

        elif query_type == 'count':
            if not table_name:
                return "[ERROR] count requires table_name"
            if not _validate_table_name(conn, table_name):
                return f"[ERROR] Unknown table: {table_name}"
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return f"Table '{table_name}': {count} rows"

        elif query_type == 'sample':
            parts = params.split(',') if params else []
            table = parts[0].strip() if parts else table_name
            n = int(parts[1].strip()) if len(parts) > 1 else 5
            if not table:
                return "[ERROR] sample requires table_name"
            if not _validate_table_name(conn, table):
                return f"[ERROR] Unknown table: {table}"
            cursor.execute(f"SELECT * FROM {table} LIMIT {n}")
            rows = cursor.fetchall()
            if not rows:
                return f"No data in table '{table}'"
            df = pd.DataFrame([dict(row) for row in rows])
            return f"Sample {min(n, len(rows))} rows from '{table}':\n\n{df.to_string()}"

        elif query_type == 'insert':
            if not table_name or not params:
                return "[ERROR] insert requires table_name and params (format: 'col1,col2;val1,val2')"
            parts = params.split(';')
            if len(parts) != 2:
                return "[ERROR] params format should be 'col1,col2,...;val1,val2,...'"
            columns = [c.strip() for c in parts[0].split(',')]
            values = [v.strip() for v in parts[1].split(',')]

            if len(columns) != len(values):
                return f"[ERROR] column count ({len(columns)}) doesn't match value count ({len(values)})"

            placeholders = ','.join(['?' for _ in values])
            cols_str = ','.join(columns)
            insert_query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

            cursor.execute(insert_query, values)
            conn.commit()
            return f"Successfully inserted 1 row into '{table_name}'"

        elif query_type == 'update':
            if not table_name or not params:
                return "[ERROR] update requires table_name and params (format: 'col1=val1,col2=val2;WHERE condition')"
            parts = params.split(';WHERE ')
            if len(parts) != 2:
                return "[ERROR] params format should be 'col1=val1,col2=val2;WHERE condition'"

            set_clause = parts[0]
            where_clause = parts[1]
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

            cursor.execute(update_query)
            conn.commit()
            return f"Successfully updated {cursor.rowcount} row(s) in '{table_name}'"

        elif query_type == 'delete':
            if not table_name or not params:
                return "[ERROR] delete requires table_name and WHERE condition in params"
            where_clause = params
            delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"

            cursor.execute(delete_query)
            conn.commit()
            return f"Successfully deleted {cursor.rowcount} row(s) from '{table_name}'"

        elif query_type == 'list_databases':
            from tools.sql_file_ingest_tool import get_database_list
            databases = get_database_list()
            if not databases:
                return "No databases found. Upload a SQL file to create one."
            db_list = "Available Databases:\n"
            for db_name_key, info in databases.items():
                tables = info.get('tables', [])
                created = info.get('created_at', 'N/A')[:10]
                db_list += f"\n  [{db_name_key}]\n"
                db_list += f"     Created: {created}\n"
                db_list += f"     Tables: {', '.join(tables) if tables else 'None'}\n"
            return db_list

        elif query_type == 'get_schema':
            if not params:
                params = db_name
            from tools.sql_file_ingest_tool import get_database_schema
            schema = get_database_schema(params)
            if "error" in schema:
                return schema["error"]

            schema_str = f"Schema for database '{params}':\n\n"
            for table_name_key, table_info in schema.get('tables', {}).items():
                schema_str += f"TABLE: {table_name_key} ({table_info['row_count']} rows)\n"
                for col in table_info['columns']:
                    pk_indicator = "[PK] " if col['primary_key'] else ""
                    nullable = "" if col['notnull'] else "nullable"
                    schema_str += f"   {pk_indicator}{col['name']}: {col['type']} {nullable}\n"
                schema_str += "\n"
            return schema_str

        else:
            return f"Unknown operation: '{query_type}'. Valid: select, insert, update, delete, describe, list_tables, count, sample, list_databases, get_schema"

    except Exception as e:
        return f"Error executing SQL: {str(e)}"
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    print("SQL Analysis Tool with SQLite Support")
    print("Sample database created at:", DB_PATH)
    print("\nDatabase initialized with sample tables: users, products, orders")
