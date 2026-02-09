# sqlalchemy-audit-events

Repository: https://github.com/larsderidder/sqlalchemy-audit-events
SQLAlchemy session events for updating audit fields and timestamps.

## Install

```bash
pip install sqlalchemy-audit-events
```

## Usage

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_audit_events import SessionInfo, register_session_events

session: AsyncSession = ...
register_session_events(session)

session.info["session_info"].user_id = 123
session.info["session_info"].update_logging_context()
```

## Development

```bash
pip install -e .[dev]
pytest
```
