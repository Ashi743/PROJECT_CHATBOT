# SQL File Upload Feature

## Overview
Upload and manage SQLite databases created from `.sql` files. After uploading, query them using natural language through the chatbot.

## Features

### 1. Upload SQL Files
- **Supported**: Any valid `.sql` file with CREATE TABLE and INSERT statements
- **Storage**: Each file creates a separate SQLite database in `data/databases/`
- **Naming**: Database name derived from filename (e.g., `insurance.sql` → `insurance.db`)
- **Persistence**: Databases persist across sessions in `data/databases/registry.json`

### 2. Database Management
- **List**: View all uploaded databases with creation dates and table counts
- **View Schema**: See table structures, column types, and row counts
- **Delete**: Remove databases you no longer need (HITL confirmation required)
- **Multiple DBs**: Upload and query multiple databases simultaneously

### 3. Query Interface
- **Sample Queries**: Auto-generated examples for each database based on schema
- **Natural Language**: Ask the AI to run queries on specific databases
- **SQL Execution**: LLM generates and executes SELECT queries
- **HITL for Writes**: Confirmation required before any INSERT, UPDATE, DELETE operations

## Usage

### Upload via UI
1. **Sidebar** → **SQL Databases** → **Upload SQL File**
2. Choose a `.sql` file (with CREATE TABLE and INSERT statements)
3. Click "Upload SQL File"
4. View tables, schema, and suggested queries in the expanded database panel

### Query in Chat
```
"What are the top insurance policies by premium?"
[Chatbot queries the insurance.db using analyze_sql tool]

"Show me all customers from USA"
[AI generates: SELECT * FROM customers WHERE country='USA']

"Count the number of active claims"
[AI generates: SELECT COUNT(*) FROM claims WHERE status='active']
```

### Available Databases
After uploading, use `db_name` parameter to specify which database to query:
```
analyze_sql(
    query_type='select',
    query='SELECT * FROM policies LIMIT 5',
    db_name='insurance'
)
```

## SQL Tool Operations

### Query Operations
- `select` - Execute SELECT queries
- `count` - Count rows in a table
- `sample` - Show sample rows
- `describe` - Show table schema

### Management Operations
- `list_tables` - List tables in current database
- `list_databases` - List all uploaded databases
- `get_schema` - Get full schema for a database

### Write Operations (HITL required)
- `insert` - Add rows
- `update` - Modify rows
- `delete` - Remove rows

## Example SQL File Format

```sql
-- Create tables
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Insert sample data
INSERT INTO customers (customer_id, name, email) VALUES
(1, 'John Doe', 'john@example.com'),
(2, 'Jane Smith', 'jane@example.com');

INSERT INTO orders (order_id, customer_id, amount) VALUES
(1, 1, 100.00),
(2, 1, 250.50),
(3, 2, 75.25);
```

## File Structure

```
data/databases/
├── analytics.db                 # Default sample database
├── sample_insurance.db          # User-uploaded database
├── registry.json                # Database metadata and tracking
└── [other_uploads].db
```

## Registry Format (registry.json)

```json
{
  "sample_insurance": {
    "created_at": "2026-04-22T16:59:58.699093",
    "original_filename": "sample_insurance.sql",
    "file_hash": "a1b2c3d4",
    "table_count": 4,
    "tables": ["customers", "policies", "claims"]
  }
}
```

## Limitations

- SQLite only (no MySQL, PostgreSQL, etc.)
- One database per file
- File must be valid UTF-8 text
- Comments in SQL must use `--` or `/* */`
- Names are case-sensitive

## Troubleshooting

### "Database already exists" Error
- Upload uses the filename as the database name
- Rename your file before uploading (e.g., `insurance_v2.sql`)
- Or delete the existing database from the UI

### SQL Parsing Errors
- Ensure all statements end with `;`
- Check for unsupported SQL syntax
- SQLite-specific syntax required (not MySQL/PostgreSQL)

### Encoding Issues
- File must be UTF-8 encoded
- Set `PYTHONIOENCODING=utf-8` in `.env` (already done)

## Chat Examples

### Example 1: Insurance Database
```
User: "Upload my insurance data"
[Uploads insurance.sql with customers, policies, claims tables]

User: "What's the breakdown of policy types by count?"
AI: Queries the insurance.db and shows a summary

User: "Find all active policies expiring in 2025"
AI: SELECT * FROM policies WHERE status='active' AND YEAR(end_date)=2025
```

### Example 2: Sales Database
```
User: "I have quarterly sales data"
[Uploads sales_q1_2026.sql]

User: "What was the revenue by region?"
AI: Queries sales_q1_2026.db and provides analysis

User: "Show me the top 10 products by units sold"
AI: SELECT product_name, SUM(units) FROM sales GROUP BY product_name ORDER BY SUM(units) DESC LIMIT 10
```

## Integration with Backend

The SQL file upload feature integrates with:
- **Backend**: `analyze_sql` tool with new `db_name` parameter
- **Frontend**: SQL Databases section in sidebar
- **Storage**: SQLite databases + JSON registry
- **LLM**: Auto-generates queries based on schema

No changes to chat flow or message handling required.
