# Hexagonal Architecture

## Overview

The Amani backend is being refactored to follow hexagonal architecture (also known as ports and adapters architecture). This architectural pattern promotes:

- **Separation of concerns**: Business logic is isolated from infrastructure concerns
- **Testability**: Pure domain logic can be tested without external dependencies
- **Flexibility**: Easy to swap implementations (e.g., different databases, APIs)
- **Maintainability**: Clear boundaries between layers

## Architecture Layers

### 1. Domain Layer (`app/domain/`)

The core business logic and entities. This layer has no external dependencies.

- **Entities** (`entities.py`): Pure data models representing core business concepts (User, LinkToken, WalletRegistryEntry, Hold, LedgerEntry)
- **Services** (`services.py`): Business logic that doesn't belong to a single entity (LinkTokenService, PolicyEnforcer)

### 2. Ports (`app/ports/`)

Interfaces that define contracts for external dependencies. These are abstract base classes that define what operations the domain layer needs.

- `user_repository.py`: User persistence operations
- `link_token.py`: Link token management operations
- `wallet_registry.py`: Wallet registry operations
- `audit.py`: Audit logging operations

### 3. Adapters (`app/adapters/`)

Concrete implementations of ports. Different adapters can be used for different environments.

- **In-memory adapters** (`adapters/inmemory/`): Simple implementations for testing
  - `user_repo.py`: In-memory user storage
  - `link_token_repo.py`: In-memory link token storage
  - `wallet_registry.py`: In-memory wallet registry
  - `audit.py`: In-memory audit log

Future adapters will include:
- Database adapters (SQLAlchemy, Supabase)
- External service adapters (Plaid, FinCra)

### 4. Application Layer (`app/application/`)

Orchestrates use cases by coordinating domain services and adapters.

- **Use Cases** (`application/use_cases/`): Application-specific business flows
  - `create_link_token.py`: Link token creation workflow

### 5. Composition Root (`app/composition.py`)

Factory functions that wire dependencies together. Provides configured instances for:
- Testing (with in-memory adapters)
- Production (with real adapters - to be implemented)

## Benefits

1. **Testing**: Domain logic can be tested with fast, in-memory adapters
2. **Independence**: Business logic doesn't depend on frameworks or databases
3. **Flexibility**: Easy to change infrastructure without touching business logic
4. **Clear boundaries**: Each layer has a specific responsibility

## Current Status

Phase 1 (Complete):
- ✅ Domain entities defined
- ✅ Port interfaces established
- ✅ In-memory adapters for testing
- ✅ Basic domain services (LinkTokenService)
- ✅ Unit tests with in-memory adapters

Next phases:
- Add database adapters (SQLAlchemy/Supabase)
- Integrate with existing FastAPI endpoints
- Add more domain services and use cases
- Migrate existing functionality to hexagonal structure

## Testing Strategy

- **Unit tests**: Test domain logic with in-memory adapters (fast, no I/O)
- **Integration tests**: Test with real adapters (database, external APIs)
- **End-to-end tests**: Test through HTTP endpoints

## Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=app/domain --cov=app/ports
```

## References

- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [Ports and Adapters Pattern](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)
