package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/revcopy/crawlers/amazon/docs"
	"github.com/revcopy/crawlers/amazon/internal/config"
	"github.com/revcopy/crawlers/amazon/internal/handlers"
	"github.com/revcopy/crawlers/amazon/internal/middleware"
	"github.com/revcopy/crawlers/amazon/internal/services"
	ginSwagger "github.com/swaggo/gin-swagger"
	swaggerFiles "github.com/swaggo/files"
)

// @title Amazon Crawler API
// @version 1.0
// @description High-performance Amazon product scraping microservice with analytics and proxy support
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name MIT
// @license.url https://opensource.org/licenses/MIT

// @host localhost:8081
// @BasePath /

// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
// @description Type "Bearer" followed by a space and JWT token.

func main() {
	// Load configuration
	cfg := config.Load()

	// Initialize services
	proxyService := services.NewProxyService()
	scraperService := services.NewScraperService(proxyService)
	authService := services.NewAuthService(cfg.JWTSecret)
	analyticsService := services.NewAnalyticsService()

	// Initialize handlers
	h := handlers.New(scraperService, authService, analyticsService, proxyService)

	// Setup Gin router
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Logger())
	router.Use(gin.Recovery())
	router.Use(middleware.CORS())
	router.Use(middleware.RateLimit())

	// Swagger documentation endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	
	// Custom API Documentation
	router.Static("/static", "./docs")
	router.GET("/docs", func(c *gin.Context) {
		c.File("./docs/index.html")
	})
	
	// API endpoints summary
	router.GET("/api", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"service": "Amazon Crawler API",
			"version": "1.0.0",
			"status":  "running",
			"endpoints": gin.H{
				"documentation": gin.H{
					"swagger_ui":     "/swagger/index.html",
					"custom_docs":    "/docs",
					"openapi_spec":   "/swagger/doc.json",
					"yaml_spec":      "/static/swagger.yaml",
				},
				"authentication": gin.H{
					"login":   "POST /api/v1/auth/login",
					"refresh": "POST /api/v1/auth/refresh",
				},
				"scraping": gin.H{
					"single_product": "POST /api/v1/amazon/scrape",
					"bulk_scrape":    "POST /api/v1/amazon/bulk-scrape",
					"search":         "POST /api/v1/amazon/search",
					"get_product":    "GET /api/v1/amazon/product/:asin",
				},
				"analytics": gin.H{
					"stats":       "GET /api/v1/analytics/stats",
					"performance": "GET /api/v1/analytics/performance",
					"track_event": "POST /api/v1/analytics/track",
				},
				"proxy": gin.H{
					"configure": "POST /api/v1/proxy/configure",
					"status":    "GET /api/v1/proxy/status",
					"test":      "POST /api/v1/proxy/test",
				},
				"user_management": gin.H{
					"create_user":  "POST /api/v1/users",
					"list_users":   "GET /api/v1/users",
					"get_user":     "GET /api/v1/users/:username",
					"update_user":  "PUT /api/v1/users/:username",
					"delete_user":  "DELETE /api/v1/users/:username",
					"get_user_proxy": "GET /api/v1/users/:username/proxy",
				},
				"proxy_management": gin.H{
					"create_proxy":   "POST /api/v1/proxies",
					"list_proxies":   "GET /api/v1/proxies",
					"get_proxy":      "GET /api/v1/proxies/:proxy_id",
					"update_proxy":   "PUT /api/v1/proxies/:proxy_id",
					"delete_proxy":   "DELETE /api/v1/proxies/:proxy_id",
				},
				"proxy_assignments": gin.H{
					"assign_proxy":     "POST /api/v1/proxy-assignments",
					"list_assignments": "GET /api/v1/proxy-assignments",
					"unassign_proxy":   "DELETE /api/v1/proxy-assignments/:username",
				},
			},
			"default_users": gin.H{
				"admin":     "admin123",
				"crawler":   "crawler123",
				"analytics": "analytics123",
			},
		})
	})

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().UTC(),
			"service":   "amazon-crawler",
		})
	})

	// API routes
	api := router.Group("/api/v1")
	{
		// Authentication
		auth := api.Group("/auth")
		{
			auth.POST("/login", h.Login)
			auth.POST("/refresh", h.RefreshToken)
		}

		// Protected routes
		protected := api.Group("/")
		protected.Use(middleware.AuthRequired(authService))
		{
			// Amazon scraping endpoints
			amazon := protected.Group("/amazon")
			{
				amazon.POST("/scrape", h.ScrapeAmazonProduct)
				amazon.POST("/bulk-scrape", h.BulkScrapeAmazonProducts)
				amazon.GET("/product/:asin", h.GetAmazonProduct)
				amazon.POST("/search", h.SearchAmazonProducts)
			}

			// Analytics endpoints
			analytics := protected.Group("/analytics")
			{
				analytics.GET("/stats", h.GetAnalyticsStats)
				analytics.GET("/performance", h.GetPerformanceMetrics)
				analytics.POST("/track", h.TrackEvent)
			}

			// Legacy proxy management (keep for compatibility)
			proxy := protected.Group("/proxy")
			{
				proxy.POST("/configure", h.ConfigureProxy)
				proxy.GET("/status", h.GetProxyStatus)
				proxy.POST("/test", h.TestProxy)
			}

			// User management endpoints
			users := protected.Group("/users")
			{
				users.POST("/", h.CreateUser)                     // Create user
				users.GET("/", h.ListUsers)                       // List all users
				users.GET("/:username", h.GetUser)                // Get user by username
				users.PUT("/:username", h.UpdateUser)             // Update user
				users.DELETE("/:username", h.DeleteUser)          // Delete user
				users.GET("/:username/proxy", h.GetUserProxy)     // Get user's assigned proxy
			}

			// Enhanced proxy management endpoints
			proxies := protected.Group("/proxies")
			{
				proxies.POST("/", h.CreateProxy)                  // Create proxy
				proxies.GET("/", h.ListProxies)                   // List all proxies
				proxies.GET("/:proxy_id", h.GetProxy)             // Get proxy by ID
				proxies.PUT("/:proxy_id", h.UpdateProxy)          // Update proxy
				proxies.DELETE("/:proxy_id", h.DeleteProxy)       // Delete proxy
			}

			// Proxy assignment endpoints
			proxyAssignments := protected.Group("/proxy-assignments")
			{
				proxyAssignments.POST("/", h.AssignProxyToUser)           // Assign proxy to user
				proxyAssignments.GET("/", h.ListUserProxyAssignments)     // List all assignments
				proxyAssignments.DELETE("/:username", h.UnassignProxyFromUser) // Unassign proxy from user
			}
		}
	}

	// Create HTTP server
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      router,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in a goroutine
	go func() {
		log.Printf("Amazon Crawler API starting on port %s", cfg.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server exited")
} 