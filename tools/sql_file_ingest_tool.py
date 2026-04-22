from pathlib import Path
import sqlite3
import json
from datetime import datetime
import hashlib

DB_DIR = Path(__file__).parent.parent / "data" / "databases"
DB_DIR.mkdir(parents=True, exist_ok=True)
REGISTRY_PATH = DB_DIR / "registry.json"


def load_registry() -> dict:
    """Load the database registry"""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, 'r') as f:
            return json.load(f)
    return {}


def save_registry(registry: dict):
    """Save the database registry"""
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)


def get_file_hash(content: bytes) -> str:
    """Generate hash of file content"""
    return hashlib.md5(content).hexdigest()[:8]


def parse_sql_file(sql_content: str) -> list[str]:
    """Parse SQL file into individual statements"""
    statements = []
    current_statement = ""

    for line in sql_content.split('\n'):
        # Skip comments
        if line.strip().startswith('--'):
            continue
        if line.strip().startswith('/*'):
            continue

        current_statement += line + "\n"

        # Statement ends with semicolon
        if ';' in line:
            stmt = current_statement.strip()
            if stmt:
                statements.append(stmt)
            current_statement = ""

    # Add any remaining statement
    if current_statement.strip():
        statements.append(current_statement.strip())

    return statements


def ingest_sql_file(file_bytes: bytes, file_name: str) -> dict:
    """
    Ingest a SQL file and create a new SQLite database

    Args:
        file_bytes: Raw file content
        file_name: Original filename (e.g., "insurance.sql")

    Returns:
        {
            "status": "ok" or "error",
            "message": str,
            "db_name": str (without .db extension),
            "tables": list,
            "statements_executed": int
        }
    """
    try:
        # Parse filename
        if not file_name.endswith('.sql'):
            return {
                "status": "error",
                "message": "File must be a .sql file"
            }

        db_name = file_name.rsplit('.', 1)[0]  # Remove .sql extension
        db_path = DB_DIR / f"{db_name}.db"

        # Check if database already exists
        if db_path.exists():
            return {
                "status": "error",
                "message": f"Database '{db_name}' already exists. Please use a different filename."
            }

        # Parse SQL content
        sql_content = file_bytes.decode('utf-8')
        statements = parse_sql_file(sql_content)

        if not statements:
            return {
                "status": "error",
                "message": "No SQL statements found in file"
            }

        # Create database and execute statements
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        executed_count = 0
        table_names = []
        errors = []

        for stmt in statements:
            if not stmt.strip():
                continue

            try:
                cursor.execute(stmt)
                executed_count += 1

                # Track CREATE TABLE statements
                if 'CREATE TABLE' in stmt.upper():
                    # Extract table name
                    tokens = stmt.upper().split()
                    if 'TABLE' in tokens:
                        idx = tokens.index('TABLE')
                        if idx + 1 < len(tokens):
                            table_name = tokens[idx + 1].strip('`"')
                            table_names.append(table_name)
            except Exception as e:
                errors.append(f"Error executing statement: {str(e)}")

        conn.commit()

        # Get table info from database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        actual_tables = [row[0] for row in cursor.fetchall()]

        conn.close()

        # Register database
        registry = load_registry()
        registry[db_name] = {
            "created_at": datetime.now().isoformat(),
            "original_filename": file_name,
            "file_hash": get_file_hash(file_bytes),
            "table_count": len(actual_tables),
            "tables": actual_tables
        }
        save_registry(registry)

        message = f"Successfully created database '{db_name}' with {len(actual_tables)} table(s)"
        if errors:
            message += f"\n⚠️ {len(errors)} statement(s) had warnings"

        return {
            "status": "ok",
            "message": message,
            "db_name": db_name,
            "tables": actual_tables,
            "statements_executed": executed_count,
            "warnings": errors if errors else None
        }

    except UnicodeDecodeError:
        return {
            "status": "error",
            "message": "File must be valid UTF-8 text"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing file: {str(e)}"
        }


def get_database_list() -> dict:
    """Get list of all uploaded databases"""
    registry = load_registry()
    return registry


def get_database_schema(db_name: str) -> dict:
    """Get detailed schema for a database"""
    registry = load_registry()

    if db_name not in registry:
        return {"error": f"Database '{db_name}' not found"}

    db_path = DB_DIR / f"{db_name}.db"
    if not db_path.exists():
        return {"error": f"Database file not found for '{db_name}'"}

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        schema_info = {
            "db_name": db_name,
            "tables": {}
        }

        # Get info for each table
        for table_name in registry[db_name].get("tables", []):
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            col_info = []
            for cid, name, col_type, notnull, dflt_value, pk in columns:
                col_info.append({
                    "name": name,
                    "type": col_type,
                    "notnull": bool(notnull),
                    "default": dflt_value,
                    "primary_key": bool(pk)
                })

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            schema_info["tables"][table_name] = {
                "columns": col_info,
                "row_count": row_count
            }

        conn.close()
        return schema_info

    except Exception as e:
        return {"error": f"Error reading schema: {str(e)}"}


def delete_database(db_name: str) -> dict:
    """Delete a database and remove from registry"""
    try:
        registry = load_registry()

        if db_name not in registry:
            return {"status": "error", "message": f"Database '{db_name}' not found in registry"}

        db_path = DB_DIR / f"{db_name}.db"

        # Delete file
        if db_path.exists():
            db_path.unlink()

        # Remove from registry
        del registry[db_name]
        save_registry(registry)

        return {
            "status": "ok",
            "message": f"Database '{db_name}' deleted successfully"
        }
    except Exception as e:
        return {"status": "error", "message": f"Error deleting database: {str(e)}"}


if __name__ == "__main__":
    print("SQL File Ingest Tool")
    print(f"Database directory: {DB_DIR}")
    print(f"Registry path: {REGISTRY_PATH}")
