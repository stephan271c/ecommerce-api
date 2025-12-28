# E-Commerce API

Production-ready RESTful API for an e-commerce platform built with FastAPI.

## Features

- **User Management**: Registration, authentication, profile management
- **Listings**: Create and manage product listings with filtering and sorting
- **JWT Authentication**: Secure token-based authentication with role-based access control
- **Rate Limiting**: Redis-based sliding window rate limiting (with in-memory fallback)
- **Health Checks**: Load balancer integration endpoints

## Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Redis (optional, for rate limiting)

### Installation

```bash
# Clone and navigate to project
cd w12d2

# Install dependencies
uv sync

# Run the development server
uv run uvicorn src.main:app --reload
```

### API Documentation

Once running, access the interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Register a new user |
| POST | `/v1/auth/login` | Login and get JWT token |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/users` | List users (paginated) |
| GET | `/v1/users/me` | Get current user profile |
| GET | `/v1/users/{id}` | Get user by ID |
| PUT | `/v1/users/{id}` | Update user |
| DELETE | `/v1/users/{id}` | Delete user |

### Listings
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/listings` | Create listing |
| GET | `/v1/listings` | List listings (filtered, sorted, paginated) |
| GET | `/v1/listings/{id}` | Get listing by ID |
| PUT | `/v1/listings/{id}` | Update listing |
| DELETE | `/v1/listings/{id}` | Delete listing |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed status with dependencies |

## Configuration

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL=sqlite:///./ecommerce.db  # Or PostgreSQL URL
SECRET_KEY=your-secret-key-change-in-production
REDIS_URL=redis://localhost:6379
```

## Docker

```bash
# Build and run with Docker Compose
docker compose up --build
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Project Structure

```
w12d2/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── config.py         # Settings and configuration
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # ORM models (User, Listing)
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # JWT authentication
│   ├── exceptions.py     # Custom exceptions
│   ├── middleware.py     # Request ID, logging
│   ├── rate_limit.py     # Redis rate limiting
│   ├── health.py         # Health check endpoints
│   └── routers/
│       ├── auth.py       # Auth endpoints
│       ├── users.py      # User CRUD
│       ├── listings.py   # Listing CRUD
│       └── external.py   # Async/background tasks demo
├── tests/
│   ├── conftest.py       # Pytest fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_listings.py
│   └── test_health.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## License

MIT
