# RevCopy Backend

This directory contains the FastAPI backend application for RevCopy - an AI-powered content generation platform.

## Project Structure

```
backend/
├── app/                    # FastAPI application
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core configuration and utilities
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic schemas for validation
│   └── services/          # Business logic services
├── alembic/               # Database migrations
├── tests/                 # Unit and integration tests
├── requirements.txt       # Python dependencies
├── run.py                # Development server runner
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker services orchestration
└── alembic.ini           # Alembic migration configuration
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (optional)

### Development Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up database:**
   ```bash
   # Start PostgreSQL and Redis (or use Docker)
   docker-compose up postgres redis -d
   
   # Run migrations
   alembic upgrade head
   ```

5. **Start development server:**
   ```bash
   python run.py
   ```

### Docker Setup

1. **Start all services:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f api
   ```

3. **Run migrations in container:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## API Documentation

Once the server is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Key Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- User registration and login
- Token refresh mechanism

### Product Management
- Multi-platform support (Amazon, eBay, AliExpress)
- Product URL validation and data extraction
- Review analysis and sentiment scoring

### Content Generation
- AI-powered marketing content creation
- Multiple content types (ads, captions, descriptions)
- Campaign management
- Bulk generation capabilities

### Background Processing
- Celery workers for async tasks
- Redis queues for task management
- Scheduled tasks with Celery Beat

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Maximum line length: 88 characters

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_main.py
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | Environment name | `development` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - User logout

### Products
- `POST /api/v1/products/` - Add new product
- `GET /api/v1/products/` - List user products
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products/{id}/analyze` - Analyze product reviews

### Content Generation
- `POST /api/v1/generation/generate` - Generate content
- `GET /api/v1/generation/content` - List generated content
- `GET /api/v1/generation/content/{id}` - Get specific content

### Campaigns
- `POST /api/v1/campaigns/` - Create campaign
- `GET /api/v1/campaigns/` - List campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. 