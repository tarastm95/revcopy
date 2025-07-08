# Amazon Crawler Makefile

.PHONY: help build run test clean docker-build docker-run docker-stop logs deps

# Default target
help:
	@echo "Amazon Crawler Microservice"
	@echo ""
	@echo "Available commands:"
	@echo "  build        Build the Go binary"
	@echo "  run          Run the application locally"
	@echo "  test         Run tests"
	@echo "  clean        Clean build artifacts"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"
	@echo "  docker-stop  Stop Docker Compose"
	@echo "  logs         Show Docker logs"
	@echo "  deps         Download dependencies"

# Build the Go binary
build:
	@echo "Building Amazon Crawler..."
	go build -o bin/amazon-crawler ./main.go

# Run the application locally
run:
	@echo "Starting Amazon Crawler..."
	go run main.go

# Run tests
test:
	@echo "Running tests..."
	go test -v ./...

# Clean build artifacts
clean:
	@echo "Cleaning..."
	rm -rf bin/
	go clean

# Download dependencies
deps:
	@echo "Downloading dependencies..."
	go mod download
	go mod tidy

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t amazon-crawler:latest .

# Run with Docker Compose
docker-run:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d

# Stop Docker Compose
docker-stop:
	@echo "Stopping Docker Compose services..."
	docker-compose down

# Show Docker logs
logs:
	@echo "Showing logs..."
	docker-compose logs -f amazon-crawler

# Development setup
dev-setup: deps
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

# Production build
prod-build:
	@echo "Building for production..."
	CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags '-w -s' -o bin/amazon-crawler ./main.go

# Install tools
install-tools:
	@echo "Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/swaggo/swag/cmd/swag@latest

# Lint code
lint:
	@echo "Running linter..."
	golangci-lint run

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Security check
security:
	@echo "Running security check..."
	go list -json -m all | nancy sleuth

# Benchmark
benchmark:
	@echo "Running benchmarks..."
	go test -bench=. -benchmem ./...

# Coverage
coverage:
	@echo "Running test coverage..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

# All checks (lint, test, security)
check: lint test security

# Generate Swagger documentation
swagger:
	@echo "Generating Swagger documentation..."
	swag init -g main.go -o ./docs

# View API documentation
docs:
	@echo "API Documentation available at:"
	@echo "  Custom Docs:    http://localhost:8081/docs"
	@echo "  Swagger UI:     http://localhost:8081/swagger/index.html"
	@echo "  API Summary:    http://localhost:8081/api"
	@echo "  YAML Spec:      http://localhost:8081/static/swagger.yaml"

# Quick start for development
dev: dev-setup docker-run logs

# Complete setup with documentation
setup: deps swagger build docs
	@echo "Amazon Crawler setup complete!" 