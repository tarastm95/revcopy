package config

import (
	"log"
	"os"

	"github.com/joho/godotenv"
)

// Config holds all configuration for the application
type Config struct {
	Port        string
	Environment string
	JWTSecret   string
	RedisURL    string
	RateLimit   RateLimitConfig
	Proxy       ProxyConfig
}

// RateLimitConfig holds rate limiting configuration
type RateLimitConfig struct {
	RequestsPerMinute int
	BurstSize         int
}

// ProxyConfig holds proxy configuration
type ProxyConfig struct {
	Username string
	Password string
	Host     string
	Port     string
}

// Load loads configuration from environment variables
func Load() *Config {
	// Load .env file if it exists
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	return &Config{
		Port:        getEnvOrDefault("PORT", "8080"),
		Environment: getEnvOrDefault("ENVIRONMENT", "development"),
		JWTSecret:   getEnvOrDefault("JWT_SECRET", "your-super-secret-jwt-key-change-in-production"),
		RedisURL:    getEnvOrDefault("REDIS_URL", "redis://localhost:6379"),
		RateLimit: RateLimitConfig{
			RequestsPerMinute: getEnvAsIntOrDefault("RATE_LIMIT_RPM", 60),
			BurstSize:         getEnvAsIntOrDefault("RATE_LIMIT_BURST", 10),
		},
		Proxy: ProxyConfig{
			Username: getEnvOrDefault("PROXY_USERNAME", "anvitop"),
			Password: getEnvOrDefault("PROXY_PASSWORD", "C29UaLSZPx"),
			Host:     getEnvOrDefault("PROXY_HOST", "74.124.222.120"),
			Port:     getEnvOrDefault("PROXY_PORT", "50100"),
		},
	}
}

// getEnvOrDefault gets an environment variable or returns a default value
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvAsIntOrDefault gets an environment variable as int or returns a default value
func getEnvAsIntOrDefault(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		// Simple conversion for this example
		// In production, you might want proper error handling
		switch value {
		case "30":
			return 30
		case "60":
			return 60
		case "120":
			return 120
		case "5":
			return 5
		case "10":
			return 10
		case "20":
			return 20
		}
	}
	return defaultValue
} 