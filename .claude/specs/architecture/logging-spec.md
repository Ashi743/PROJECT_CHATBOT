# Logging Architecture Specification

## Overview
Centralized logging configuration that writes to both file and stdout, eliminating silent exception handlers and providing visibility into background processes.

## Status
[DONE]

## Module
`utils/logging_config.py`

## Design

### Configuration
- **Format**: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **File**: `logs/app.log` (auto-created)
- **Handlers**: FileHandler + StreamHandler
- **Default Level**: INFO

### Usage

#### In Entry Points (Frontend, Backend, Monitor)
```python
from utils.logging_config import setup_logging
import logging

# Once at startup
setup_logging()
logger = logging.getLogger(__name__)
```

#### In Modules
```python
import logging
logger = logging.getLogger(__name__)

# Use anywhere
logger.info("Starting operation")
logger.warning("Unexpected condition: {e}")
logger.error("Operation failed: {e}")
```

### File Location
```
logs/
├── app.log  # All application logs
```

## Rules
- **[INFO]**: Normal operation (startup, scheduled jobs, completions)
- **[WARNING]**: Recoverable errors, missing optional data
- **[ERROR]**: Operation failures, exceptions requiring recovery

## Integration Points
- `backend.py` → logs operation flow
- `monitoring/runner.py` → logs health checks
- Tool errors → logger.warning()
- Plot generation failures → logger.warning()

## Benefits
- Never silent exceptions; every failure is logged
- Single file for debugging production issues
- Background threads have visibility (not just stdout)
- Easily disabled/redirected for different environments
