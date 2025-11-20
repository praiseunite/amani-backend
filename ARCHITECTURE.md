# Architecture Documentation

## Hexagonal Architecture (Ports & Adapters)

The Amani backend is being refactored to follow hexagonal architecture principles, which separates the core business logic from external dependencies. This makes the code more testable, maintainable, and allows easier swapping of infrastructure components.

### Architecture Layers

```
┌──────────────────────────────────────────────────────────────┐
│                     Adapters (External)                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   FastAPI      │  │   Supabase     │  │   External     │ │
│  │   Routes       │  │   Database     │  │   APIs         │ │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘ │
└───────────┼──────────────────┼──────────────────┼──────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                        Ports (Interfaces)                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │  UserRepo      │  │  LinkToken     │  │  WalletReg     │ │
│  │  Port          │  │  Port          │  │  Port          │ │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘ │
└───────────┼──────────────────┼──────────────────┼──────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                     Domain (Core Business Logic)              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Entities     │  │   Services     │  │  Use Cases     │ │
│  │   (Models)     │  │   (Logic)      │  │  (Workflow)    │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
app/
├── domain/              # Core business logic (framework-agnostic)
│   ├── entities.py      # Domain entities (User, LinkToken, etc.)
│   └── services.py      # Domain services (business rules)
│
├── ports/               # Interfaces for external dependencies
│   ├── user_repository.py
│   ├── link_token.py
│   ├── wallet_registry.py
│   └── audit.py
│
├── application/         # Use cases and orchestration
│   └── use_cases/
│       └── create_link_token.py
│
├── adapters/            # Implementations of ports
│   ├── inmemory/        # In-memory implementations (testing)
│   │   ├── user_repo.py
│   │   ├── link_token_repo.py
│   │   ├── wallet_registry.py
│   │   └── audit.py
│   └── persistence/     # Database implementations (future)
│
├── composition.py       # Dependency injection setup
│
└── routes/              # FastAPI routes (existing)
```

### Key Principles

1. **Domain Independence**: The domain layer (entities and services) has no dependencies on frameworks, databases, or external libraries. It contains pure business logic.

2. **Ports as Contracts**: Ports are abstract interfaces that define what the domain needs from the outside world. They are defined in the domain layer.

3. **Adapters as Implementations**: Adapters implement the ports and handle communication with external systems (databases, APIs, etc.).

4. **Dependency Inversion**: Dependencies point inward. The domain doesn't depend on infrastructure; infrastructure depends on domain interfaces.

5. **Testability**: Pure domain logic can be tested with in-memory adapters, without needing databases or external services.

### Domain Entities

- **User**: Represents a platform user
- **LinkToken**: Token for connecting external wallets
- **WalletRegistryEntry**: Record of connected wallets
- **Hold**: Fund holds in escrow
- **LedgerEntry**: Accounting ledger entries

### Domain Services

- **LinkTokenService**: Manages creation and consumption of link tokens
- **PolicyEnforcer**: Enforces business policies (token expiry, security rules)

### Current Ports

- **UserRepositoryPort**: User persistence operations
- **LinkTokenPort**: Link token operations
- **WalletRegistryPort**: Wallet registration operations
- **AuditPort**: Audit logging operations

### Testing Strategy

The hexagonal architecture enables multiple testing levels:

1. **Unit Tests**: Test domain logic with in-memory adapters (no database needed)
2. **Integration Tests**: Test with real database adapters
3. **End-to-End Tests**: Test through HTTP API endpoints

### Migration Strategy

This is Phase 1 of the migration:

- ✅ Create domain entities and services
- ✅ Define ports (interfaces)
- ✅ Implement in-memory adapters for testing
- ✅ Add unit tests for domain logic
- 🔄 Future: Add database adapters (Phase 2)
- 🔄 Future: Refactor existing routes to use domain layer (Phase 3)
- 🔄 Future: Replace existing CRUD with port implementations (Phase 4)

### Benefits

1. **Maintainability**: Clear separation of concerns makes code easier to understand and modify
2. **Testability**: Domain logic can be tested independently of infrastructure
3. **Flexibility**: Easy to swap implementations (e.g., change databases, add caching)
4. **Team Collaboration**: Different teams can work on different layers independently
5. **Future-Proofing**: Core business logic is isolated from technology choices
