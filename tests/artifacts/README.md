# Test Artifacts

This directory contains generated code and test output from agent validation runs.

## api/

Output from Test 1.2 (FastAPI-developer routing validation):

- **main.py** — FastAPI application factory with lifespan management
- **config.py** — Pydantic settings for database configuration
- **v1/routers/users.py** — GET /api/v1/users/search endpoint with pagination, validation, async database access
- **v1/models/** — Pydantic response schemas and ORM models
- **db/session.py** — Async SQLAlchemy session factory
- **tests/** — 17 test cases covering happy path, edge cases, and validation errors

This is a reference implementation demonstrating:
- Pydantic v2 advanced patterns (computed fields, generics, frozen models, from_attributes)
- FastAPI dependency injection and async patterns
- Clear escalation boundaries (when to involve python-pro, database-optimizer, devops-engineer, etc.)

See `docs/mece-audit/ROUTING_VALIDATION_TESTS.md` for Test 1.2 details and results.

## Other Artifacts

Additional test outputs from routing validation runs will be organized here as they are generated.
