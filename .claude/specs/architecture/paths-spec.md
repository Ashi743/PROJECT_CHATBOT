# Paths Architecture Specification

## Overview
Central path constants for the application to avoid scattered path definitions and enable consistent data directory structure across all modules.

## Status
[DONE]

## Module
`utils/paths.py`

## Design

### Directory Structure
```
PROJECT_ROOT/
├── data/
│   ├── uploads/          # User-uploaded CSV/Excel files
│   ├── databases/        # SQLite database files
│   ├── chroma_db/        # ChromaDB vector store
│   ├── plots/            # Generated visualization plots
│   └── runtime_state.json # Runtime flags (git-ignored)
```

### Path Constants
```python
PROJECT_ROOT   # Repository root
DATA_DIR       # data/ directory
UPLOADS_DIR    # For user uploads
DATABASES_DIR  # For SQLite databases
CHROMA_DIR     # For ChromaDB persistence
PLOTS_DIR      # For visualization outputs
```

## Usage

### Import
```python
from utils.paths import CHROMA_DIR, PLOTS_DIR, DATABASES_DIR, UPLOADS_DIR
```

### Example
```python
db_path = DATABASES_DIR / "analytics.db"
plot_file = PLOTS_DIR / "histogram.png"
```

## Benefits
- Single source of truth for path configuration
- Automatic directory creation on import
- Consistent across all modules
- Easy to override for deployment (testing, Docker)

## Integration Points
- sql_analysis_tool.py → DATABASES_DIR
- csv_ingest_tool.py → CHROMA_DIR, UPLOADS_DIR
- plot_utils.py → PLOTS_DIR
- retention cleanup → PLOTS_DIR
