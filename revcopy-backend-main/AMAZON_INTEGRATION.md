# Amazon Crawler Integration

This document explains how the Amazon crawler Go microservice is integrated with the RevCopy backend.

## Architecture Overview

The system now consists of:

1. **Python Backend (FastAPI)** - Main API server with AI content generation
2. **Amazon Crawler (Go)** - Microservice for scraping Amazon products and reviews
3. **Frontend (React)** - User interface

## Amazon Crawler Service

### Location and Setup

- **Path**: `crawlers/amazon/`
- **Language**: Go
- **Port**: 8080
- **Authentication**: JWT-based with default users

### Default Credentials

```
admin:admin123 (full access)
crawler:crawler123 (scraping access)
analytics:analytics123 (analytics access)
```

### Key Endpoints

- `POST /api/v1/amazon/scrape` - Scrape single Amazon product
- `POST /api/v1/amazon/bulk-scrape` - Scrape up to 10 products
- `GET /api/v1/amazon/product/:asin` - Get product by ASIN
- `POST /api/v1/amazon/search` - Search Amazon products
- `GET /health` - Health check

## Integration Features

### 1. Targeted Review Collection

The system automatically collects:
- **15 positive reviews** (4-5 stars)
- **15 negative reviews** (1-2 stars)

This provides balanced analysis for AI content generation.

### 2. Automatic Platform Detection

URLs are automatically detected:
- Amazon: `amazon.com`, `amazon.co.uk`, etc.
- Shopify: `myshopify.com`, `/products/` paths
- Others: eBay, AliExpress (mock data for now)

### 3. Fallback System

If the Amazon crawler fails:
1. Logs the error
2. Falls back to mock review data
3. Continues content generation process

## Configuration

### Backend Environment Variables

Add to your `.env` file:

```bash
# Amazon Crawler Service
AMAZON_CRAWLER_URL=http://localhost:8080
AMAZON_CRAWLER_TIMEOUT=30
AMAZON_CRAWLER_USERNAME=crawler
AMAZON_CRAWLER_PASSWORD=crawler123
```

### Docker Configuration

See `docker-compose.yml` for running both services together.

## Running the Services

### Option 1: Manual Startup

1. **Start Amazon Crawler**:
```bash
cd crawlers/amazon
make run
# or
go run main.go
```

2. **Start Python Backend**:
```bash
cd backend
python run.py
```

3. **Start Frontend**:
```bash
cd frontend
npm run dev
```

### Option 2: Docker Compose

```bash
cd backend
docker-compose up
```

## API Flow

### Product Analysis Flow

1. **Frontend** → `POST /api/v1/products/analyze`
2. **Backend** detects Amazon URL
3. **Backend** → Amazon Crawler `/api/v1/amazon/scrape`
4. **Amazon Crawler** returns product data + reviews
5. **Backend** filters 15 positive + 15 negative reviews
6. **Backend** stores product data in database
7. **Frontend** redirects to content generation

### Content Generation Flow

1. **Frontend** → `POST /api/v1/intelligent/generate`
2. **Backend** uses product data + targeted reviews
3. **AI Service** generates content based on review analysis
4. **Backend** returns generated content
5. **Frontend** displays content with options to save

## Monitoring and Health Checks

### Health Check Endpoints

- Backend: `GET /health`
- Amazon Crawler: `GET /health`
- Frontend: Available on configured port

### Logging

All services use structured logging:
- **Backend**: JSON logs with correlation IDs
- **Amazon Crawler**: Structured logs with request tracking
- **Frontend**: Console logging for development

## Error Handling

### Amazon Crawler Failures

1. **Network Issues**: Automatic retry with exponential backoff
2. **Authentication Errors**: Re-authenticate and retry
3. **Rate Limiting**: Respect rate limits and queue requests
4. **Service Down**: Fall back to mock data and continue

### Product Detection Issues

1. **Invalid URLs**: Clear error messages to user
2. **Unsupported Platforms**: Graceful fallback
3. **No Reviews Found**: Continue with product data only

## Performance Optimization

### Review Collection

- Parallel processing of positive and negative reviews
- Intelligent filtering based on rating scores
- Caching of frequently accessed products

### API Optimization

- Connection pooling for HTTP requests
- JWT token caching and refresh
- Concurrent request processing

## Security Considerations

### Authentication

- JWT tokens with expiration
- Service-to-service authentication
- Rate limiting on all endpoints

### Data Privacy

- No storage of personal reviewer information
- Anonymized review data processing
- GDPR-compliant data handling

## Troubleshooting

### Common Issues

1. **Amazon Crawler Not Starting**
   - Check port 8080 availability
   - Verify Go installation
   - Check firewall settings

2. **Authentication Failures**
   - Verify credentials in environment variables
   - Check Amazon crawler service logs
   - Ensure service is running on correct port

3. **No Reviews Returned**
   - Check product URL validity
   - Verify Amazon crawler can access the product
   - Review rate limiting settings

4. **Content Generation Fails**
   - Check AI service configuration
   - Verify DeepSeek API key
   - Review backend logs for errors

### Log Locations

- **Backend**: Console output and structured logs
- **Amazon Crawler**: Service logs in Go format
- **Database**: PostgreSQL logs

## Development and Testing

### Testing Amazon Integration

1. Use test Amazon URLs with known review patterns
2. Mock the Amazon crawler for unit tests
3. Integration tests with real crawler service

### Development Workflow

1. Start services in development mode
2. Use hot reload for rapid iteration
3. Monitor logs across all services
4. Test with various Amazon product types

## Deployment Considerations

### Production Setup

1. Use environment-specific configurations
2. Implement proper secret management
3. Set up monitoring and alerting
4. Configure load balancing if needed

### Scaling

- Amazon crawler can be scaled horizontally
- Backend can handle multiple crawler instances
- Database connection pooling for high load

## Support and Maintenance

### Regular Maintenance

1. Update Go dependencies for Amazon crawler
2. Monitor API rate limits and adjust
3. Review and rotate authentication credentials
4. Update mock data for fallback scenarios

### Monitoring Metrics

- Request success rates
- Response times
- Error rates by service
- Review collection efficiency 