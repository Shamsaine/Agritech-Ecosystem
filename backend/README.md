# Agritech Intelligence Platform - Backend

FastAPI backend for the Agritech Ecosystem Intelligence Platform.

## ⚠️ Important Security Notes

- **Never commit `.env` file to version control** - Use `.gitignore`
- **Never hardcode credentials** in source code
- **Never share passwords** via email or chat
- **Rotate credentials regularly** in production
- **Use strong, unique passwords** for all environments
- Treat all database credentials as sensitive data

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Installation](#installation)
- [Database Management](#database-management)
- [Running the Application](#running-the-application)
- [Development](#development)
- [Testing](#testing)
- [Making Migrations](#making-migrations)
- [Database Inspection](#database-inspection)
- [Notes](#notes)

## Prerequisites

### Required Software

- **Python 3.13+** - https://www.python.org/
- **Docker & Docker Compose** - https://www.docker.com/products/docker-desktop
- **PostgreSQL 17** (runs in Docker, not required locally)
- **Git** - https://git-scm.com/

### Optional

- **Make** (for Windows, WSL or Git Bash recommended)
- **pgAdmin** or **DBeaver** for visual database inspection

## Environment Setup

### 1. Clone and Navigate

```bash
git clone <repository>
cd Agritech-Ecosystem
cd backend
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Environment Variables

Create a `.env` file in the `backend/` directory with your configuration:

```env
APP_NAME=Your Application Name
APP_ENV=development
DEBUG=true

POSTGRES_HOST=localhost
POSTGRES_PORT=<your_postgres_port>
POSTGRES_DB=<your_database_name>
POSTGRES_USER=<your_database_user>
POSTGRES_PASSWORD=<your_secure_password>
```

**Important:** 
- Never commit `.env` to version control (already in `.gitignore`)
- Contact your team lead for production credentials
- Use strong, unique passwords in non-development environments
- See `.env.example` for reference configuration (if available)

## Installation

### 1. Install Python Dependencies

```bash
uv pip install -e ".[dev]"
```

Or with pip directly:

```bash
pip install -r requirements.txt
```

For development dependencies:

```bash
pip install pytest pytest-asyncio httpx
```

### 2. Start PostgreSQL

Start the PostgreSQL container:

```bash
docker compose up -d postgres
```

Verify it's running:

```bash
docker compose ps
```

You should see the postgres service with status `Up`.

View logs:

```bash
docker compose logs -f postgres
```

Or use the Make command:

```bash
make db-up
make db-logs
```

### 3. Initialize the Database

Run all pending migrations:

```bash
uv run alembic upgrade head
```

Or use Make:

```bash
make migrate
```

This creates all required tables for Phase 1:
- `technologies`
- `categories`
- `focus_areas`
- `platforms`
- `languages`
- `access_types`
- `availability_statuses`
- `physical_components`

## Running the Application

### Start the Development Server

```bash
uv run uvicorn app.main:app --reload
```

Or use Make:

```bash
make dev
```

The API will be available at: **http://localhost:8000**

### Useful Endpoints

- **Health Check:** `GET http://localhost:8000/health`
- **Database Health:** `GET http://localhost:8000/health/database`
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── health.py
│   ├── core/
│   │   └── config.py
│   ├── db/
│   │   ├── base.py
│   │   ├── health.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── mixins.py
│   │       └── reference.py
│   ├── schemas/
│   │   └── health.py
│   └── main.py
├── migrations/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py
│   └── test_database.py
├── main.py
├── pyproject.toml
├── alembic.ini
└── README.md
```

### Development Workflow

1. **Start the application:** `make dev`
2. **Run tests in another terminal:** `make test`
3. **Check logs:** `make db-logs`

### Code Style

- **Python 3.13** syntax
- **Type hints** for all functions
- **SQLAlchemy 2.0** async patterns
- **Pydantic** for schema validation

## Testing

### Run All Tests

```bash
uv run pytest
```

Or use Make:

```bash
make test
```

### Run Specific Tests

```bash
uv run pytest tests/test_database.py::TestDatabaseConnection -v
```

### Test Output

Expected output for Phase 1 (7 tests):

```
tests/test_database.py::TestDatabaseConnection::test_database_connection PASSED
tests/test_database.py::TestRequiredFields::test_create_technology_without_name PASSED
tests/test_database.py::TestUniqueConstraints::test_duplicate_slug_raises_error PASSED
tests/test_database.py::TestUniqueConstraints::test_duplicate_name_raises_error PASSED
tests/test_database.py::TestTransactionRollback::test_transaction_rollback PASSED
tests/test_database.py::TestHealthEndpoint::test_database_health_endpoint PASSED
tests/test_database.py::TestHealthEndpoint::test_health_endpoint PASSED

================================ 7 passed ================================
```

### Test Database

- Tests automatically use a separate database instance
- Credentials are configured internally and do not require `.env` configuration
- Database is created automatically on first test run
- Cleaned up after tests complete
- Never affects development or production databases

## Making Migrations

### Create a New Migration

When you modify models, create a migration to update the database schema:

```bash
uv run alembic revision --autogenerate -m "Add user table"
```

Or use Make:

```bash
make migration message="Add user table"
```

This creates a new file in `migrations/versions/` with the changes.

### Review the Migration

Always review the generated migration file before applying:

```bash
cat migrations/versions/xxxx_add_user_table.py
```

### Apply Migrations

```bash
uv run alembic upgrade head
```

Or use Make:

```bash
make migrate
```

### Rollback a Migration

```bash
# Rollback one version
uv run alembic downgrade -1

# Rollback to a specific version
uv run alembic downgrade <revision>
```

### View Migration History

```bash
uv run alembic history
```

## Database Inspection

### Using psql Command Line

Connect directly to the database using credentials from your `.env` file:

```bash
psql -h ${POSTGRES_HOST} -p ${POSTGRES_PORT} -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

You'll be prompted for the password. Use the value from `POSTGRES_PASSWORD` in your `.env` file.

Useful commands in psql:
```sql
-- List all tables
\dt

-- Describe a table
\d technologies

-- Run a query
SELECT * FROM technologies;

-- Exit
\q
```

### Using pgAdmin (Optional)

1. Install pgAdmin locally or run in Docker
2. Connect to: `${POSTGRES_HOST}:${POSTGRES_PORT}` (from your `.env`)
3. Username: `${POSTGRES_USER}`
4. Password: `${POSTGRES_PASSWORD}`
5. Database: `${POSTGRES_DB}`

### Using Python REPL

```python
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def inspect():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT * FROM technologies"))
        for row in result:
            print(row)

asyncio.run(inspect())
```

## Configuration

### Environment Variables

All configuration is loaded from environment variables in your `.env` file:

| Variable | Purpose | Example |
|----------|---------|---------|
| `APP_NAME` | Application display name | `Agritech Intelligence Platform` |
| `APP_ENV` | Environment type | `development`, `testing`, `production` |
| `DEBUG` | Enable debug mode | `true` or `false` |
| `POSTGRES_HOST` | Database hostname | `localhost` or `db.example.com` |
| `POSTGRES_PORT` | Database port | Varies by setup |
| `POSTGRES_DB` | Database name | Your database name |
| `POSTGRES_USER` | Database user | Your database user |
| `POSTGRES_PASSWORD` | Database password | **Keep secret, never commit** |

### Security Notes

- **Never** hardcode credentials in code
- **Never** commit `.env` to version control
- Use strong passwords in production
- Rotate credentials regularly
- Use secret management services in production (AWS Secrets Manager, HashiCorp Vault, etc.)

## Troubleshooting

### PostgreSQL Won't Start

```bash
# Check if port is already in use
docker compose ps

# Remove containers and volumes if needed
docker compose down -v
docker compose up -d postgres
```

### Migration Conflicts

```bash
# Check current migration state
uv run alembic current

# Stamp to the current state if needed
uv run alembic stamp head
```

### Tests Failing

```bash
# Ensure test database exists
uv run pytest -v

# Check logs
docker compose logs postgres
```

### Database Connection Error

1. Verify `.env` file exists and has all required variables
2. Check PostgreSQL is running: `docker compose ps`
3. Verify credentials match PostgreSQL configuration
4. Ensure network connectivity to database host
5. Check firewall and port access

## Notes

### Phase 1 Completion

Phase 1 includes:
- ✅ Database schema with 8 reference tables
- ✅ Request-session lifecycle implementation
- ✅ Comprehensive test suite (7 tests)
- ✅ Health check endpoints
- ✅ Database connection validation

See `PHASE1_COMPLETION.md` for details (not committed to git).

### Research Data

Research data has **not yet been imported**. The database currently contains only the schema.

Future phases will:
1. Import research datasets
2. Build API endpoints for querying data
3. Implement filtering and search
4. Add authentication and authorization
5. Deploy to production

### Database Constraints

All tables enforce:
- ✅ Unique `name` and `slug` fields
- ✅ `is_active` status tracking
- ✅ Automatic `created_at` and `updated_at` timestamps
- ✅ UUID primary keys
- ✅ NOT NULL constraints on required fields

## Quick Start Checklist

- [ ] Install Python 3.13+
- [ ] Install Docker Desktop
- [ ] Clone repository
- [ ] Create `.env` file
- [ ] Run `docker compose up -d postgres`
- [ ] Run `uv run alembic upgrade head`
- [ ] Run `uv run pytest` to verify setup
- [ ] Run `make dev` to start server
- [ ] Visit http://localhost:8000/docs

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `make db-logs`
3. Run tests to verify setup: `make test`
4. Check Swagger UI for API documentation: http://localhost:8000/docs
