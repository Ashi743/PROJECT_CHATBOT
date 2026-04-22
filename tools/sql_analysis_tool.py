from langchain_core.tools import tool
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import json

DB_DIR = Path(__file__).parent.parent / "data" / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "analytics.db"

def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def _initialize_sample_database():
    """Create sample database if it doesn't exist"""
    if DB_PATH.exists():
        return

    conn = get_connection()
    cursor = conn.cursor()

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

    now = datetime.now()
    users_data = [
        (1, 'john_doe', 'john@example.com', (now - timedelta(days=30)).isoformat(), 'USA'),
        (2, 'jane_smith', 'jane@example.com', (now - timedelta(days=25)).isoformat(), 'UK'),
        (3, 'bob_wilson', 'bob@example.com', (now - timedelta(days=20)).isoformat(), 'Canada'),
        (4, 'alice_johnson', 'alice@example.com', (now - timedelta(days=15)).isoformat(), 'Australia'),
        (5, 'charlie_brown', 'charlie@example.com', (now - timedelta(days=10)).isoformat(), 'USA'),
    ]
    cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?)", users_data)

    products_data = [
        (1, 'Laptop', 'Electronics', 999.99, 5, (now - timedelta(days=60)).isoformat()),
        (2, 'Mouse', 'Electronics', 29.99, 50, (now - timedelta(days=60)).isoformat()),
        (3, 'Keyboard', 'Electronics', 79.99, 30, (now - timedelta(days=60)).isoformat()),
        (4, 'Monitor', 'Electronics', 299.99, 10, (now - timedelta(days=60)).isoformat()),
        (5, 'USB Cable', 'Accessories', 9.99, 100, (now - timedelta(days=60)).isoformat()),
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", products_data)

    orders_data = [
        (1, 1, 1, 1, 999.99, (now - timedelta(days=5)).isoformat(), 'completed'),
        (2, 2, 2, 2, 59.98, (now - timedelta(days=3)).isoformat(), 'completed'),
        (3, 1, 3, 1, 79.99, (now - timedelta(days=2)).isoformat(), 'pending'),
        (4, 3, 4, 1, 299.99, (now - timedelta(days=1)).isoformat(), 'completed'),
        (5, 4, 5, 5, 49.95, (now - timedelta(hours=12)).isoformat(), 'pending'),
        (6, 2, 1, 1, 999.99, (now - timedelta(hours=6)).isoformat(), 'processing'),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", orders_data)

    conn.commit()
    conn.close()

_initialize_sample_database()

@tool
def analyze_sql(query_type: str, table_name: str = "", query: str = "", params: str = "") -> str:
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

    Returns:
        Formatted string result of the query

    Examples:
        - analyze_sql(query_type='select', query='SELECT * FROM users WHERE country="USA"')
        - analyze_sql(query_type='describe', table_name='orders')
        - analyze_sql(query_type='count', table_name='users')
        - analyze_sql(query_type='insert', table_name='users', params='username,email,country;new_user,new@example.com,India')
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if query_type == 'select':
            if not query:
                return "Error: select requires SQL query"
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return f"No results found for query"
            df = pd.DataFrame([dict(row) for row in rows])
            return f"Query Results:\n\n{df.to_string()}"

        elif query_type == 'describe':
            if not table_name:
                return "Error: describe requires table_name"
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            if not columns:
                return f"Error: Table '{table_name}' not found"
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
                return "Error: count requires table_name"
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            return f"Table '{table_name}': {count} rows"

        elif query_type == 'sample':
            parts = params.split(',') if params else []
            table = parts[0].strip() if parts else table_name
            n = int(parts[1].strip()) if len(parts) > 1 else 5
            if not table:
                return "Error: sample requires table_name"
            cursor.execute(f"SELECT * FROM {table} LIMIT {n}")
            rows = cursor.fetchall()
            if not rows:
                return f"No data in table '{table}'"
            df = pd.DataFrame([dict(row) for row in rows])
            return f"Sample {min(n, len(rows))} rows from '{table}':\n\n{df.to_string()}"

        elif query_type == 'insert':
            if not table_name or not params:
                return "Error: insert requires table_name and params (format: 'col1,col2;val1,val2')"
            parts = params.split(';')
            if len(parts) != 2:
                return "Error: params format should be 'col1,col2,...;val1,val2,...'"
            columns = [c.strip() for c in parts[0].split(',')]
            values = [v.strip() for v in parts[1].split(',')]

            if len(columns) != len(values):
                return f"Error: column count ({len(columns)}) doesn't match value count ({len(values)})"

            placeholders = ','.join(['?' for _ in values])
            cols_str = ','.join(columns)
            insert_query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

            cursor.execute(insert_query, values)
            conn.commit()
            return f"Successfully inserted 1 row into '{table_name}'"

        elif query_type == 'update':
            if not table_name or not params:
                return "Error: update requires table_name and params (format: 'col1=val1,col2=val2;WHERE condition')"
            parts = params.split(';WHERE ')
            if len(parts) != 2:
                return "Error: params format should be 'col1=val1,col2=val2;WHERE condition'"

            set_clause = parts[0]
            where_clause = parts[1]
            update_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

            cursor.execute(update_query)
            conn.commit()
            return f"Successfully updated {cursor.rowcount} row(s) in '{table_name}'"

        elif query_type == 'delete':
            if not table_name or not params:
                return "Error: delete requires table_name and WHERE condition in params"
            where_clause = params
            delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"

            cursor.execute(delete_query)
            conn.commit()
            return f"Successfully deleted {cursor.rowcount} row(s) from '{table_name}'"

        else:
            return f"Unknown operation: '{query_type}'. Valid: select, insert, update, delete, describe, list_tables, count, sample"

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
