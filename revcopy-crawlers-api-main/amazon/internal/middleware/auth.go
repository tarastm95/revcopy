package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/revcopy/crawlers/amazon/internal/services"
)

// AuthRequired middleware validates JWT tokens
func AuthRequired(authService *services.AuthService) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error":   "Authorization header required",
				"code":    "AUTH_HEADER_MISSING",
				"message": "Please provide an Authorization header with Bearer token",
			})
			c.Abort()
			return
		}

		// Extract token from "Bearer <token>"
		parts := strings.Split(authHeader, " ")
		if len(parts) != 2 || strings.ToLower(parts[0]) != "bearer" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error":   "Invalid authorization header format",
				"code":    "AUTH_HEADER_INVALID",
				"message": "Authorization header must be in format: Bearer <token>",
			})
			c.Abort()
			return
		}

		token := parts[1]
		claims, err := authService.ValidateToken(token)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error":   "Invalid or expired token",
				"code":    "TOKEN_INVALID",
				"message": err.Error(),
			})
			c.Abort()
			return
		}

		// Store user information in context
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Next()
	}
} 