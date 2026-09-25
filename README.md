# Snapshot Checkpoint Service

A Flask project demonstrating snapshots and checkpoints for state recovery.

## Features
- Versioned key/value state
- Named immutable checkpoints
- Restore state from a checkpoint
- List, inspect and delete checkpoints
- Thread-safe implementation
- Health and statistics endpoints
- Pytest tests

## Run
```bash
pip install -r requirements.txt
python app.py
```

## API
- `PUT /api/state`
- `GET /api/state`
- `POST /api/checkpoints`
- `GET /api/checkpoints`
- `GET /api/checkpoints/<checkpoint_id>`
- `POST /api/checkpoints/<checkpoint_id>/restore`
- `DELETE /api/checkpoints/<checkpoint_id>`
- `GET /api/stats`
- `GET /health`

## Concepts
Checkpointing, snapshots, rollback, state recovery, immutable snapshots, versioning and fault recovery.
