# SQL Analyst Spec Sheet

## Purpose
Query and analyze SQLite databases with 10+ operations: select, insert, update, delete, describe, list tables.
Supports uploaded SQL files (schema + data).
Sample database included (users, products, orders).

## Status
[DONE]

## Trigger Phrases
- "select all users from the database"
- "how many orders are there"
- "show me the table schema"
- "what tables exist in the database"
- "get sample data from products"
- "list all uploaded databases"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query_type | str | yes | none | Operation type (see Operations table) |
| db_name | str | no | analytics | Database name |
| table_name | str | no | varies | Table name (for describe, insert, update, delete) |
| query | str | no | varies | SQL SELECT statement |
| params | str | no | varies | Operation-specific parameters |

## Operations (11 supported)
| Operation | Params | Output |
|-----------|--------|--------|
| select | SQL SELECT statement | Query results as DataFrame |
| describe | table_name | Column names, types, nullability, primary keys |
| list_tables | none | All tables in database |
| count | table_name | Row count |
| sample | "table_name,N" | N random sample rows |
| insert | "col1,col2;val1,val2" | Rows inserted count |
| update | "col=val;WHERE condition" | Rows updated count |
| delete | "WHERE condition" | Rows deleted count |
| list_databases | none | All uploaded databases with metadata |
| get_schema | db_name | Full schema: tables, columns, row counts |

## Output Format
Query Results:

    user_id  username     email                created_at
0   1        john_doe     john@example.com     2026-03-23
1   2        jane_smith   jane@example.com     2026-03-28
2   3        bob_wilson   bob@example.com      2026-04-02

Table: users

Columns:
  user_id: INTEGER (NOT NULL) PRIMARY KEY
  username: TEXT (NOT NULL)
  email: TEXT (NOT NULL)
  created_at: TIMESTAMP
  country: TEXT (nullable)

Available Databases:

  [sales_2024]
     Created: 2026-04-10
     Tables: orders, customers, products

  [insurance]
     Created: 2026-04-15
     Tables: policies, claims, agents

## Sample Database
Default "analytics" database includes:
- users (5 rows): user_id, username, email, created_at, country
- products (5 rows): product_id, product_name, category, price, stock
- orders (6 rows): order_id, user_id, product_id, quantity, total_price, order_date, status

## Dependencies
- sqlite3 (Python stdlib)
- pandas (pip: pandas)
- langchain_core.tools

## HITL
Conditional:
- SELECT queries → NO HITL (read-only)
- INSERT/UPDATE/DELETE → YES HITL (data modification)
- DESCRIBE/LIST operations → NO HITL (read-only)

## Chaining
Combines with:
- csv_analyst → "upload CSV, import to SQL, then query"
- web_search → "find benchmark data, compare with database results"

## Known Issues
- No transactions/rollback yet (single execute commits)
- Insert/update/delete uses positional parameters (?) - no SQL injection vulnerability
- Large result sets (>1000 rows) truncate display
- PRAGMA calls for schema may vary by SQLite version

## Test Command
python -c "
from tools.sql_analysis_tool import analyze_sql
# List tables
print(analyze_sql.invoke({
    'query_type': 'list_tables',
    'db_name': 'analytics'
}))

# Select query
print(analyze_sql.invoke({
    'query_type': 'select',
    'query': 'SELECT * FROM users LIMIT 5',
    'db_name': 'analytics'
}))
"

## Bunge Relevance
Data warehouse queries for supply chain optimization, customer analytics, and transaction analysis.

## Internal Notes
- Databases stored in data/databases/ as SQLite .db files
- Registry in data/databases/registry.json tracks uploaded DBs
- sqlite3.Row factory returns dict-like rows
- Pandas DataFrame output for easy formatting
- SQL file ingestion via sql_file_ingest_tool (separate tool)
- Connection pooling handled per query (no persistent connection)
- Insert uses VALUES (?,?,...) to prevent injection
