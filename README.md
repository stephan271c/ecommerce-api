# E-Commerce API

Production-ready RESTful API for an e-commerce platform built with FastAPI.

## Features

- **Web Frontend**: Jinja2 template-based UI for browsing and managing the platform
- **User Management**: Registration, authentication, profile management
- **Listings**: Create and manage product listings with filtering and sorting
- **JWT Authentication**: Secure token-based authentication with role-based access control (RBAC) - `user` and `admin` roles
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
cd ecommerce-api

# Install dependencies
uv sync

# Run the development server
uv run uvicorn src.main:app --reload
```

### API Documentation

Once running, access the interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Web Frontend

A lightweight Jinja2-based frontend is available at http://localhost:8000/

| Route | Description |
|-------|-------------|
| `/` | Home page with platform overview |
| `/login` | User login form |
| `/register` | New user registration |
| `/listings` | Browse listings with filters |
| `/listings/new` | Create new listing (auth required) |
| `/listings/{id}` | View listing details |
| `/listings/{id}/edit` | Edit listing (owner only) |
| `/profile` | User profile page (auth required) |
| `/users` | Users list (auth required) |
| `/random-user` | Random User Generator (External API demo) |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/register` | Register a new user |
| POST | `/v1/auth/login` | Login and get JWT token |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/users` | List users (Admin only) |
| GET | `/v1/users/me` | Get current user profile |
| GET | `/v1/users/{id}` | Get user by ID (Self or Admin only) |
| PUT | `/v1/users/{id}` | Update user (Self or Admin only) |
| PUT | `/v1/users/{id}/role` | Update user role (Admin only) |
| DELETE | `/v1/users/{id}` | Delete user (Self or Admin only) |

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

### External
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/external/random-user` | Fetch random user from external API (Rate limited: 5 req/60s) |
| POST | `/v1/external/background-task` | Start a background task (returns task ID) |

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

## Railway Deployment

Deploy to [Railway](https://railway.app) with these steps:

### 1. Create a New Project

1. Connect your GitHub repository to Railway
2. Railway will auto-detect the `Dockerfile` and `railway.json`

### 2. Add Required Services

Add these plugins from the Railway dashboard:
- **PostgreSQL** - For production database
- **Redis** - For rate limiting (optional, app falls back to in-memory)

### 3. Configure Environment Variables

In your Railway service's **Variables** section, add:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | Auto-filled by PostgreSQL plugin | Or set manually |
| `SECRET_KEY` | Generate with `openssl rand -hex 32` | **Required for production** |
| `REDIS_URL` | Auto-filled by Redis plugin | Optional |
| `JWT_ALGORITHM` | `HS256` | Default works fine |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Adjust as needed |
| `RATE_LIMIT_REQUESTS` | `100` | Requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Window duration |
| `APP_NAME` | `E-Commerce API` | Optional |
| `DEBUG` | `False` | **Keep False in production** |

> **Note**: See `.env.railway.example` for a complete template.

### 4. Deploy

Railway auto-deploys on git push. Monitor the deployment logs in the Railway dashboard.

### Health Check

Railway uses `/health` for health checks (configured in `railway.json`).


## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Scripts

Utility scripts for administrative tasks are located in the `scripts/` directory.

### Create Admin User

Create an admin account with elevated privileges:

```bash
# Interactive mode (recommended - password hidden)
uv run python -m scripts.create_admin

# Command-line arguments
uv run python -m scripts.create_admin --email admin@example.com --username admin --password YourPass123
```

Password requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

## Project Structure

```
w12d2/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── routers/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── listings.py
│   │       ├── health.py
│   │       ├── external.py
│   │       └── frontend.py      # Jinja2 template routes
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── exceptions.py
│   ├── middleware/
│   │   └── middleware.py
│   ├── models/
│   │   └── models.py
│   ├── schemas/
│   │   └── schemas.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── cache.py
│   │   └── rate_limit.py
│   ├── static/                   # Frontend assets
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/                # Jinja2 templates
│       ├── base.html
│       ├── index.html
│       ├── random_user.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── listings/
│       │   ├── list.html
│       │   ├── detail.html
│       │   └── form.html
│       └── users/
│           ├── profile.html
│           └── list.html
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_listings.py
│   ├── test_health.py
│   ├── test_external.py          # External API and background tasks
│   ├── test_cache.py             # Caching functionality
│   └── test_rate_limit.py        # Rate limiting tests
├── scripts/
│   └── create_admin.py           # CLI tool to create admin users
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## License

MIT
