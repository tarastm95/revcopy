package middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/time/rate"
)

// RateLimiter stores rate limiters for different IPs
type RateLimiter struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(r rate.Limit, b int) *RateLimiter {
	return &RateLimiter{
		limiters: make(map[string]*rate.Limiter),
		rate:     r,
		burst:    b,
	}
}

// GetLimiter returns a rate limiter for the given IP
func (rl *RateLimiter) GetLimiter(ip string) *rate.Limiter {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	limiter, exists := rl.limiters[ip]
	if !exists {
		limiter = rate.NewLimiter(rl.rate, rl.burst)
		rl.limiters[ip] = limiter
	}

	return limiter
}

// RateLimit middleware implements rate limiting
func RateLimit() gin.HandlerFunc {
	// Create rate limiter: 60 requests per minute with burst of 10
	rl := NewRateLimiter(rate.Every(time.Minute/60), 10)

	// Cleanup old limiters every 5 minutes
	go func() {
		ticker := time.NewTicker(5 * time.Minute)
		defer ticker.Stop()

		for range ticker.C {
			rl.mu.Lock()
			// Clear all limiters (simple cleanup strategy)
			rl.limiters = make(map[string]*rate.Limiter)
			rl.mu.Unlock()
		}
	}()

	return func(c *gin.Context) {
		ip := c.ClientIP()
		limiter := rl.GetLimiter(ip)

		if !limiter.Allow() {
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":   "Rate limit exceeded",
				"code":    "RATE_LIMIT_EXCEEDED",
				"message": "Too many requests. Please try again later.",
			})
			c.Abort()
			return
		}

		c.Next()
	}
} 