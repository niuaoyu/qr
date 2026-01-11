# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WorldQuant Brain Alpha 回测系统 - A multi-machine, multi-threaded backtesting system for alpha expressions with automatic deduplication via fingerprinting and MySQL-based distributed coordination.

**Key Features:**
- Multi-account support (lab, mylab, ubuntu, backup)
- Multi-threaded concurrent backtesting with semaphore-based API rate limiting
- Multi-machine collaboration via MySQL + Tailscale VPN
- Automatic deduplication using SHA256 fingerprints
- Expression filtering with regex-based rules
- Graceful shutdown with Ctrl+C

---

## Architecture Overview

### Core Data Flow

```
batch_config.json
    ↓
loaders/json_loader.py (generate payloads)
    ↓
loaders/expression_filter.py (filter forbidden patterns)
    ↓
core/fingerprint.py (SHA256 hash of expression + settings)
    ↓
storage/database.py (check if fingerprint exists in DB)
    ↓
core/simulation.py (submit to WorldQuant API with 429 retry)
    ↓
core/backtest_engine.py (poll results, get alpha details)
    ↓
storage/database.py (save to SQLite/MySQL)
    ↓
storage/file_writer.py (export results to TXT)
```

### Module Responsibilities

| Module | Purpose | Key Files |
|--------|---------|-----------|
| **config** | Global settings, paths, database config | `settings.py` |
| **core** | Backtesting engine, auth, fingerprinting, logging | `backtest_engine.py`, `simulation.py`, `fingerprint.py` |
| **loaders** | JSON parsing, expression filtering, TXT conversion | `json_loader.py`, `expression_filter.py` |
| **storage** | Database operations (SQLite/MySQL), file I/O, backups | `database.py`, `file_writer.py` |

### Concurrency Model

**Semaphore Strategy (Semaphore only controls API submission):**
- `submit_simulation()` - **inside semaphore** (limited to MAX_WORKERS)
- `poll_simulation_result()` - **outside semaphore** (unlimited parallel polling)
- `get_alpha_detail()` - **outside semaphore** (unlimited parallel fetching)

**Rationale:** WorldQuant limits concurrent *running* backtests, not polling requests. After submission succeeds, semaphore is released immediately, allowing other threads to submit new tasks while previous ones poll results.

### Multi-Machine Architecture

```
Ubuntu (100.84.80.8) - MySQL Host + Worker
    ↓ Tailscale VPN
    ├─ Windows B (lab, 100.103.93.93) - Worker
    ├─ Windows A (mylab, 100.110.126.49) - Worker
    └─ Ubuntu - Worker
```

Each machine:
1. Loads local `batch_config.json`
2. Generates fingerprints
3. Queries shared MySQL to check if already tested
4. Submits only new alphas
5. Results written to shared MySQL

---

## Common Development Tasks

### Running the System

```bash
# Setup
cp .env.example .env
# Edit .env: set USER_CHOICE, DB_TYPE, DB_HOST

# Install dependencies
pip install pymysql python-dotenv

# Run main backtesting loop
python main.py

# Convert TXT expressions to JSON config
python convert_txt.py

# Test database connection
python test_connection.py

# Migrate SQLite to MySQL
python migrate_to_mysql.py

# Run frontend API server
cd front_demonstration && python server.py
```

### Testing Database Connectivity

```bash
python test_connection.py
```

Verifies connection to configured database (SQLite or MySQL based on `.env`).

### Debugging a Single Alpha

Edit `batch_config.json` to contain only the expression you want to test, then run `python main.py`.

### Checking Fingerprint Collisions

Query the database directly:
```python
from storage import get_connection, check_exists
conn = get_connection()
exists = check_exists(conn, fingerprint_hash)
```

### Viewing Backups

```python
from storage import list_backups
backups = list_backups()
for backup in backups:
    print(backup)
```

### Restoring from Backup

```python
from storage import restore_database
restore_database('io/mysql_backups/worldquant.20260105_220600.sql')
```

---

## Configuration

### .env Variables

```
USER_CHOICE=lab                    # Account: lab, mylab, ubuntu, backup
DB_TYPE=mysql                      # Database: sqlite or mysql
DB_HOST=100.84.80.8               # MySQL host IP
DB_PORT=3306                       # MySQL port
DB_USER=wq_user                    # MySQL username
DB_PASSWORD=NAYnay232408.          # MySQL password
DB_NAME=worldquant                 # Database name
```

### batch_config.json Format

```json
{
  "alpha_templates": [
    "rank(ts_rank(vwap, 20))",
    "rank(ts_rank(close, 20))"
  ],
  "template_params": {
    "field": ["close", "vwap"],
    "period": [10, 20]
  },
  "settings_base": {
    "neutralization": "market",
    "delay": 1,
    "decay": 0,
    "universe": "top3000",
    "truncation": 0.05,
    "region": "US",
    "nan_handling": "drop",
    "instrument_type": "stock",
    "unit_handling": "long_short",
    "pasteurization": "daily"
  },
  "settings_params": {
    "decay": [0, 3, 5],
    "delay": [1, 2]
  }
}
```

### filter_rules.json Format

Add forbidden expression patterns:
```json
{
  "forbidden_templates": [
    {
      "template": "No division by zero",
      "regex": ".*\\/\\s*0.*",
      "description": "Prevents division by literal zero"
    }
  ]
}
```

---

## Key Implementation Details

### Fingerprint Generation (core/fingerprint.py)

Fingerprint = SHA256(expression | neutralization | delay | decay | universe | truncation | region | nan_handling | instrument_type | unit_handling | pasteurization)

This ensures identical expressions with identical settings produce the same fingerprint, enabling deduplication across machines.

### API Rate Limiting (core/simulation.py)

WorldQuant API returns 429 (Too Many Requests) when concurrent limit exceeded. Automatic retry strategy:
- Attempt 1: wait 10s
- Attempt 2: wait 15s
- Attempt 3: wait 20s
- Fail after 3 attempts

### Database Schema (storage/database.py)

**Table: alpha_is**
- `fingerprint` (VARCHAR, PRIMARY KEY) - SHA256 hash
- `expression` (TEXT) - Alpha expression
- `alpha_id` (VARCHAR) - WorldQuant alpha ID
- `grade` (VARCHAR) - Alpha grade
- `sharpe` (FLOAT) - Sharpe ratio
- `fitness` (FLOAT) - Fitness score
- `user` (VARCHAR) - Account that submitted
- `created_at` (TIMESTAMP) - Submission time

### Graceful Shutdown (core/graceful_exit.py)

Press Ctrl+C to trigger graceful shutdown:
- Stops accepting new tasks
- Waits for in-flight tasks to complete
- Prints summary statistics
- Exits cleanly

---

## Important Constraints

### File Operations

- **Always use dedicated tools** instead of shell commands:
  - Read files: `Read` tool (not `cat`, `head`, `tail`)
  - Edit files: `Edit` tool (not `sed`, `awk`)
  - Create files: `Write` tool (not `echo >`, `cat <<EOF`)
  - Search files: `Glob` tool (not `find`, `ls`)
  - Search content: `Grep` tool (not `grep`, `rg`)

### Code Style

- Minimal, efficient code with no redundancy
- Comments only when logic isn't self-evident
- No docstrings unless absolutely necessary
- Only make changes directly requested; avoid "improvements"

### Git Operations

- **Read-only:** `git log`, `git status`, `git diff`, `git branch`, `git show`
- **Forbidden:** `git commit`, `git push`, `git pull`, `git merge`, `git rebase`, `git reset`

### Language

- **With tools/models:** English
- **With user:** Chinese (中文)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 429 errors | Check WorldQuant web UI; system auto-retries with exponential backoff |
| Connection timeout | Verify Tailscale VPN is active; check MySQL host IP in `.env` |
| Permission denied | Verify MySQL user has GRANT privileges on worldquant database |
| Fingerprint collision | Check if expression + settings combination already exists in DB |
| Graceful exit not working | Ensure `core/graceful_exit.py` is imported in main loop |

---

## Related Documentation

- [config/config.md](config/config.md) - Configuration module details
- [core/core.md](core/core.md) - Core module architecture
- [loaders/loaders.md](loaders/loaders.md) - Loader module details
- [storage/storage.md](storage/storage.md) - Storage and backup system
- [front_demonstration/front_demonstration.md](front_demonstration/front_demonstration.md) - Frontend API server
