# Amazon Crawler Microservice

A high-performance Amazon product scraping microservice built with Go and Gin framework.

## Features

- **High Performance**: Built with Go for maximum throughput and minimal latency
- **Proxy Support**: Configurable proxy support for avoiding IP blocks
- **Authentication**: JWT-based authentication system
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Analytics**: Comprehensive analytics and performance metrics
- **Bulk Scraping**: Support for bulk product scraping
- **Product Search**: Amazon product search functionality
- **Docker Support**: Fully containerized for easy deployment

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token

### Amazon Scraping
- `POST /api/v1/amazon/scrape` - Scrape single product
- `POST /api/v1/amazon/bulk-scrape` - Bulk scrape products
- `GET /api/v1/amazon/product/:asin` - Get cached product data
- `POST /api/v1/amazon/search` - Search Amazon products

### Analytics
- `GET /api/v1/analytics/stats` - Get analytics statistics
- `GET /api/v1/analytics/performance` - Get performance metrics
- `POST /api/v1/analytics/track` - Track custom events

### Proxy Management
- `POST /api/v1/proxy/configure` - Configure proxy settings
- `GET /api/v1/proxy/status` - Get proxy status
- `POST /api/v1/proxy/test` - Test proxy connection

### Health Check
- `GET /health` - Service health check

## Quick Start

### Prerequisites
- Go 1.21 or later
- Redis (optional, for caching)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crawlers/amazon
```

2. Install dependencies:
```bash
go mod download
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`

5. Run the service:
```bash
go run main.go
```

The service will start on `http://localhost:8080`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t amazon-crawler .
```

2. Run with Docker:
```bash
docker run -p 8080:8080 --env-file .env amazon-crawler
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8080` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `JWT_SECRET` | JWT signing secret | `your-super-secret-jwt-key-change-in-production` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `RATE_LIMIT_RPM` | Requests per minute limit | `60` |
| `RATE_LIMIT_BURST` | Burst limit | `10` |
| `PROXY_USERNAME` | Proxy username | `anvitop` |
| `PROXY_PASSWORD` | Proxy password | `C29UaLSZPx` |
| `PROXY_HOST` | Proxy host | `74.124.222.120` |
| `PROXY_PORT` | Proxy port | `50100` |

## Usage Examples

### Login
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Scrape Single Product
```bash
curl -X POST http://localhost:8080/api/v1/amazon/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "url": "https://www.amazon.com/dp/B08N5WRWNW"
  }'
```

### Bulk Scrape Products
```bash
curl -X POST http://localhost:8080/api/v1/amazon/bulk-scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "urls": [
      "https://www.amazon.com/dp/B08N5WRWNW",
      "https://www.amazon.com/dp/B08N5WRWN1"
    ]
  }'
```

### Search Products
```bash
curl -X POST http://localhost:8080/api/v1/amazon/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "wireless headphones",
    "page": 1
  }'
```

### Get Analytics
```bash
curl -X GET http://localhost:8080/api/v1/analytics/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Default Users

For development/testing purposes, the following users are available:

| Username | Password | Description |
|----------|----------|-------------|
| `admin` | `admin123` | Administrator user |
| `crawler` | `crawler123` | Crawler user |
| `analytics` | `analytics123` | Analytics user |

**Note**: In production, implement proper user management with a database.

## Proxy Configuration

The service supports proxy configuration for avoiding IP blocks:

```bash
curl -X POST http://localhost:8080/api/v1/proxy/configure \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "username": "anvitop",
    "password": "C29UaLSZPx",
    "host": "74.124.222.120",
    "port": "50100"
  }'
```

## Performance

- **Concurrent Requests**: Supports high concurrent request load
- **Rate Limiting**: 60 requests per minute per IP by default
- **Caching**: Redis-based caching for improved performance
- **Proxy Rotation**: Support for proxy rotation (to be implemented)

## Monitoring

The service provides comprehensive analytics:

- Total requests and success/failure rates
- Average response times
- Error distribution
- Top scraped ASINs
- Proxy usage statistics

## Error Handling

All endpoints return structured error responses:

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "message": "Detailed error message"
}
```

## Security

- JWT-based authentication
- Rate limiting
- CORS support
- Input validation
- Proxy support for IP rotation

## Production Deployment

1. Set `ENVIRONMENT=production`
2. Change `JWT_SECRET` to a secure random string
3. Configure Redis for caching
4. Set up reverse proxy (nginx)
5. Configure monitoring and logging
6. Set up SSL/TLS certificates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please create an issue in the repository. 