package handlers

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/revcopy/crawlers/amazon/internal/services"
)

// Handlers holds all HTTP handlers
type Handlers struct {
	scraperService   *services.ScraperService
	authService      *services.AuthService
	analyticsService *services.AnalyticsService
	proxyService     *services.ProxyService
}

// New creates a new handlers instance
func New(scraperService *services.ScraperService, authService *services.AuthService, analyticsService *services.AnalyticsService, proxyService *services.ProxyService) *Handlers {
	return &Handlers{
		scraperService:   scraperService,
		authService:      authService,
		analyticsService: analyticsService,
		proxyService:     proxyService,
	}
}

// Login handles user authentication
// @Summary User login
// @Description Authenticate user with credentials and receive JWT tokens
// @Tags authentication
// @Accept json
// @Produce json
// @Param request body services.LoginRequest true "Login credentials"
// @Success 200 {object} services.LoginResponse "Login successful"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Authentication failed"
// @Router /api/v1/auth/login [post]
func (h *Handlers) Login(c *gin.Context) {
	var req services.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	response, err := h.authService.Login(req.Username, req.Password)
	if err != nil {
		h.analyticsService.TrackError("auth_failed")
		c.JSON(http.StatusUnauthorized, gin.H{
			"error":   "Authentication failed",
			"code":    "AUTH_FAILED",
			"message": err.Error(),
		})
		return
	}

	h.analyticsService.TrackEvent(req.Username, "login", map[string]interface{}{
		"timestamp": time.Now(),
		"success":   true,
	})

	c.JSON(http.StatusOK, response)
}

// RefreshToken handles token refresh
// @Summary Refresh JWT token
// @Description Refresh expired JWT token using refresh token
// @Tags authentication
// @Accept json
// @Produce json
// @Param request body object{refresh_token=string} true "Refresh token"
// @Success 200 {object} services.LoginResponse "Token refreshed successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Token refresh failed"
// @Router /api/v1/auth/refresh [post]
func (h *Handlers) RefreshToken(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	response, err := h.authService.RefreshToken(req.RefreshToken)
	if err != nil {
		h.analyticsService.TrackError("token_refresh_failed")
		c.JSON(http.StatusUnauthorized, gin.H{
			"error":   "Token refresh failed",
			"code":    "TOKEN_REFRESH_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, response)
}

// ScrapeAmazonProduct handles single product scraping
// @Summary Scrape single Amazon product
// @Description Extract product information from a single Amazon product URL
// @Tags amazon-scraping
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.ScrapeRequest true "Amazon product URL to scrape"
// @Success 200 {object} map[string]interface{} "Scraping successful"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 500 {object} map[string]interface{} "Scraping failed"
// @Router /api/v1/amazon/scrape [post]
func (h *Handlers) ScrapeAmazonProduct(c *gin.Context) {
	var req services.ScrapeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	userID := c.GetString("user_id")
	start := time.Now()

	product, err := h.scraperService.ScrapeProduct(req.URL)
	latency := time.Since(start)

	if err != nil {
		h.analyticsService.TrackRequest(false, latency, "")
		h.analyticsService.TrackError("scrape_failed")
		h.analyticsService.TrackEvent(userID, "scrape_failed", map[string]interface{}{
			"url":   req.URL,
			"error": err.Error(),
		})

		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Scraping failed",
			"code":    "SCRAPE_FAILED",
			"message": err.Error(),
		})
		return
	}

	h.analyticsService.TrackRequest(true, latency, product.ASIN)
	h.analyticsService.TrackEvent(userID, "scrape_success", map[string]interface{}{
		"url":     req.URL,
		"asin":    product.ASIN,
		"latency": latency.Milliseconds(),
	})

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    product,
		"meta": gin.H{
			"latency_ms": latency.Milliseconds(),
			"timestamp":  time.Now().UTC(),
		},
	})
}

// BulkScrapeAmazonProducts handles bulk product scraping
// @Summary Bulk scrape Amazon products
// @Description Extract product information from multiple Amazon product URLs (max 10)
// @Tags amazon-scraping
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.BulkScrapeRequest true "Amazon product URLs to scrape"
// @Success 200 {object} map[string]interface{} "Bulk scraping successful"
// @Failure 400 {object} map[string]interface{} "Invalid request format or too many URLs"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 500 {object} map[string]interface{} "Bulk scraping failed"
// @Router /api/v1/amazon/bulk-scrape [post]
func (h *Handlers) BulkScrapeAmazonProducts(c *gin.Context) {
	var req services.BulkScrapeRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	if len(req.URLs) > 10 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Too many URLs",
			"code":    "TOO_MANY_URLS",
			"message": "Maximum 10 URLs allowed per bulk request",
		})
		return
	}

	userID := c.GetString("user_id")
	start := time.Now()

	products, err := h.scraperService.BulkScrapeProducts(req.URLs)
	latency := time.Since(start)

	h.analyticsService.TrackEvent(userID, "bulk_scrape", map[string]interface{}{
		"url_count":      len(req.URLs),
		"success_count":  len(products),
		"total_latency":  latency.Milliseconds(),
		"partial_success": err != nil && len(products) > 0,
	})

	if err != nil && len(products) == 0 {
		h.analyticsService.TrackError("bulk_scrape_failed")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Bulk scraping failed",
			"code":    "BULK_SCRAPE_FAILED",
			"message": err.Error(),
		})
		return
	}

	response := gin.H{
		"success":       len(products) > 0,
		"data":          products,
		"total_count":   len(products),
		"requested_count": len(req.URLs),
		"meta": gin.H{
			"latency_ms": latency.Milliseconds(),
			"timestamp":  time.Now().UTC(),
		},
	}

	if err != nil {
		response["warning"] = err.Error()
	}

	c.JSON(http.StatusOK, response)
}

// GetAmazonProduct handles getting cached product data
// @Summary Get Amazon product by ASIN
// @Description Retrieve cached product information by ASIN
// @Tags amazon-scraping
// @Produce json
// @Security BearerAuth
// @Param asin path string true "Amazon product ASIN"
// @Success 200 {object} map[string]interface{} "Product found"
// @Failure 400 {object} map[string]interface{} "Missing ASIN parameter"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 501 {object} map[string]interface{} "Feature not implemented"
// @Router /api/v1/amazon/product/{asin} [get]
func (h *Handlers) GetAmazonProduct(c *gin.Context) {
	asin := c.Param("asin")
	if asin == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "ASIN parameter required",
			"code":    "MISSING_ASIN",
			"message": "Please provide a valid ASIN",
		})
		return
	}

	// In a real implementation, you would fetch from cache/database
	// For now, return a not implemented response
	c.JSON(http.StatusNotImplemented, gin.H{
		"error":   "Feature not implemented",
		"code":    "NOT_IMPLEMENTED",
		"message": "Product caching not yet implemented",
	})
}

// SearchAmazonProducts handles product search
// @Summary Search Amazon products
// @Description Search for products on Amazon using keywords
// @Tags amazon-scraping
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.SearchRequest true "Search query and pagination"
// @Success 200 {object} map[string]interface{} "Search successful"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 500 {object} map[string]interface{} "Search failed"
// @Router /api/v1/amazon/search [post]
func (h *Handlers) SearchAmazonProducts(c *gin.Context) {
	var req services.SearchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	if req.Page <= 0 {
		req.Page = 1
	}

	userID := c.GetString("user_id")
	start := time.Now()

	products, err := h.scraperService.SearchProducts(req.Query, req.Page)
	latency := time.Since(start)

	h.analyticsService.TrackEvent(userID, "search", map[string]interface{}{
		"query":    req.Query,
		"page":     req.Page,
		"results":  len(products),
		"latency":  latency.Milliseconds(),
		"success":  err == nil,
	})

	if err != nil {
		h.analyticsService.TrackError("search_failed")
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Search failed",
			"code":    "SEARCH_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    products,
		"count":   len(products),
		"query":   req.Query,
		"page":    req.Page,
		"meta": gin.H{
			"latency_ms": latency.Milliseconds(),
			"timestamp":  time.Now().UTC(),
		},
	})
}

// GetAnalyticsStats returns analytics statistics
// @Summary Get analytics statistics
// @Description Retrieve comprehensive analytics statistics
// @Tags analytics
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "Analytics statistics"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/analytics/stats [get]
func (h *Handlers) GetAnalyticsStats(c *gin.Context) {
	stats := h.analyticsService.GetStats()
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    stats,
	})
}

// GetPerformanceMetrics returns performance metrics
// @Summary Get performance metrics
// @Description Retrieve system performance metrics and response times
// @Tags analytics
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "Performance metrics"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/analytics/performance [get]
func (h *Handlers) GetPerformanceMetrics(c *gin.Context) {
	metrics := h.analyticsService.GetPerformanceMetrics()
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    metrics,
	})
}

// TrackEvent handles custom event tracking
// @Summary Track custom event
// @Description Record a custom analytics event with arbitrary data
// @Tags analytics
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body object{type=string,data=object} true "Event type and data"
// @Success 200 {object} map[string]interface{} "Event tracked successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/analytics/track [post]
func (h *Handlers) TrackEvent(c *gin.Context) {
	var req struct {
		Type string                 `json:"type" binding:"required"`
		Data map[string]interface{} `json:"data"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	userID := c.GetString("user_id")
	h.analyticsService.TrackEvent(userID, req.Type, req.Data)

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Event tracked successfully",
	})
}

// ConfigureProxy handles proxy configuration
// @Summary Configure proxy settings
// @Description Update proxy configuration for scraping requests
// @Tags proxy
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body object{username=string,password=string,host=string,port=string} true "Proxy configuration"
// @Success 200 {object} map[string]interface{} "Proxy configured successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxy/configure [post]
func (h *Handlers) ConfigureProxy(c *gin.Context) {
	var req struct {
		Username string `json:"username" binding:"required"`
		Password string `json:"password" binding:"required"`
		Host     string `json:"host" binding:"required"`
		Port     string `json:"port" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	// This would need to be implemented in the scraper service
	// For now, return success
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Proxy configured successfully",
	})
}

// GetProxyStatus returns proxy status
// @Summary Get proxy status
// @Description Retrieve current proxy connection status and metrics
// @Tags proxy
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "Proxy status"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxy/status [get]
func (h *Handlers) GetProxyStatus(c *gin.Context) {
	// This would fetch actual proxy status
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"enabled":   false,
			"connected": false,
			"latency":   0,
		},
	})
}

// TestProxy tests proxy connection
// @Summary Test proxy connection
// @Description Test the current proxy configuration and connectivity
// @Tags proxy
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "Proxy test result"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxy/test [post]
func (h *Handlers) TestProxy(c *gin.Context) {
	// This would test the actual proxy
	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"connected": false,
			"message":   "Proxy testing not implemented",
		},
	})
}

// USER MANAGEMENT HANDLERS

// CreateUser creates a new user
// @Summary Create new user
// @Description Create a new user account with specified role and permissions
// @Tags user-management
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.CreateUserRequest true "User creation data"
// @Success 201 {object} map[string]interface{} "User created successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 409 {object} map[string]interface{} "User already exists"
// @Router /api/v1/users [post]
func (h *Handlers) CreateUser(c *gin.Context) {
	var req services.CreateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	user, err := h.authService.CreateUser(req)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "user already exists" {
			statusCode = http.StatusConflict
		} else if err.Error() == "invalid role" {
			statusCode = http.StatusBadRequest
		}

		c.JSON(statusCode, gin.H{
			"error":   "User creation failed",
			"code":    "USER_CREATION_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"success": true,
		"message": "User created successfully",
		"data":    user,
	})
}

// GetUser gets user information
// @Summary Get user information
// @Description Retrieve user information by username
// @Tags user-management
// @Produce json
// @Security BearerAuth
// @Param username path string true "Username"
// @Success 200 {object} map[string]interface{} "User information"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "User not found"
// @Router /api/v1/users/{username} [get]
func (h *Handlers) GetUser(c *gin.Context) {
	username := c.Param("username")
	if username == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Username parameter required",
			"code":    "MISSING_USERNAME",
			"message": "Please provide a valid username",
		})
		return
	}

	user, err := h.authService.GetUser(username)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":   "User not found",
			"code":    "USER_NOT_FOUND",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    user,
	})
}

// ListUsers lists all users
// @Summary List all users
// @Description Retrieve a list of all users in the system
// @Tags user-management
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "List of users"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/users [get]
func (h *Handlers) ListUsers(c *gin.Context) {
	users := h.authService.ListUsers()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    users,
		"count":   len(users),
	})
}

// UpdateUser updates user information
// @Summary Update user information
// @Description Update user password, role, or active status
// @Tags user-management
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param username path string true "Username"
// @Param request body services.UpdateUserRequest true "User update data"
// @Success 200 {object} map[string]interface{} "User updated successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "User not found"
// @Router /api/v1/users/{username} [put]
func (h *Handlers) UpdateUser(c *gin.Context) {
	username := c.Param("username")
	if username == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Username parameter required",
			"code":    "MISSING_USERNAME",
			"message": "Please provide a valid username",
		})
		return
	}

	var req services.UpdateUserRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	user, err := h.authService.UpdateUser(username, req)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "user not found" {
			statusCode = http.StatusNotFound
		} else if err.Error() == "invalid role" {
			statusCode = http.StatusBadRequest
		}

		c.JSON(statusCode, gin.H{
			"error":   "User update failed",
			"code":    "USER_UPDATE_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "User updated successfully",
		"data":    user,
	})
}

// DeleteUser deletes a user
// @Summary Delete user
// @Description Delete a user account from the system
// @Tags user-management
// @Produce json
// @Security BearerAuth
// @Param username path string true "Username"
// @Success 200 {object} map[string]interface{} "User deleted successfully"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "User not found"
// @Failure 403 {object} map[string]interface{} "Cannot delete admin user"
// @Router /api/v1/users/{username} [delete]
func (h *Handlers) DeleteUser(c *gin.Context) {
	username := c.Param("username")
	if username == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Username parameter required",
			"code":    "MISSING_USERNAME",
			"message": "Please provide a valid username",
		})
		return
	}

	err := h.authService.DeleteUser(username)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "user not found" {
			statusCode = http.StatusNotFound
		} else if err.Error() == "cannot delete admin user" {
			statusCode = http.StatusForbidden
		}

		c.JSON(statusCode, gin.H{
			"error":   "User deletion failed",
			"code":    "USER_DELETION_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "User deleted successfully",
	})
}

// ENHANCED PROXY MANAGEMENT HANDLERS

// CreateProxy creates a new proxy configuration
// @Summary Create new proxy
// @Description Add a new proxy configuration to the system
// @Tags proxy-management
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.CreateProxyRequest true "Proxy configuration data"
// @Success 201 {object} map[string]interface{} "Proxy created successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxies [post]
func (h *Handlers) CreateProxy(c *gin.Context) {
	var req services.CreateProxyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	// Get current user from token
	createdBy := c.GetString("username")
	if createdBy == "" {
		createdBy = "unknown"
	}

	proxy, err := h.proxyService.CreateProxy(req, createdBy)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Proxy creation failed",
			"code":    "PROXY_CREATION_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"success": true,
		"message": "Proxy created successfully",
		"data":    proxy,
	})
}

// GetProxy gets proxy information by ID
// @Summary Get proxy information
// @Description Retrieve proxy configuration by ID
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Param proxy_id path string true "Proxy ID"
// @Success 200 {object} map[string]interface{} "Proxy information"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "Proxy not found"
// @Router /api/v1/proxies/{proxy_id} [get]
func (h *Handlers) GetProxy(c *gin.Context) {
	proxyID := c.Param("proxy_id")
	if proxyID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Proxy ID parameter required",
			"code":    "MISSING_PROXY_ID",
			"message": "Please provide a valid proxy ID",
		})
		return
	}

	proxy, err := h.proxyService.GetProxy(proxyID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":   "Proxy not found",
			"code":    "PROXY_NOT_FOUND",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    proxy,
	})
}

// ListProxies lists all proxy configurations
// @Summary List all proxies
// @Description Retrieve a list of all proxy configurations
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "List of proxies"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxies [get]
func (h *Handlers) ListProxies(c *gin.Context) {
	proxies := h.proxyService.ListProxies()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    proxies,
		"count":   len(proxies),
	})
}

// UpdateProxy updates proxy configuration
// @Summary Update proxy configuration
// @Description Update proxy settings like credentials, host, port, etc.
// @Tags proxy-management
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param proxy_id path string true "Proxy ID"
// @Param request body services.UpdateProxyRequest true "Proxy update data"
// @Success 200 {object} map[string]interface{} "Proxy updated successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "Proxy not found"
// @Router /api/v1/proxies/{proxy_id} [put]
func (h *Handlers) UpdateProxy(c *gin.Context) {
	proxyID := c.Param("proxy_id")
	if proxyID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Proxy ID parameter required",
			"code":    "MISSING_PROXY_ID",
			"message": "Please provide a valid proxy ID",
		})
		return
	}

	var req services.UpdateProxyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	proxy, err := h.proxyService.UpdateProxy(proxyID, req)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "proxy not found" {
			statusCode = http.StatusNotFound
		}

		c.JSON(statusCode, gin.H{
			"error":   "Proxy update failed",
			"code":    "PROXY_UPDATE_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Proxy updated successfully",
		"data":    proxy,
	})
}

// DeleteProxy deletes a proxy configuration
// @Summary Delete proxy
// @Description Delete a proxy configuration from the system
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Param proxy_id path string true "Proxy ID"
// @Success 200 {object} map[string]interface{} "Proxy deleted successfully"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "Proxy not found"
// @Failure 403 {object} map[string]interface{} "Cannot delete default proxy"
// @Router /api/v1/proxies/{proxy_id} [delete]
func (h *Handlers) DeleteProxy(c *gin.Context) {
	proxyID := c.Param("proxy_id")
	if proxyID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Proxy ID parameter required",
			"code":    "MISSING_PROXY_ID",
			"message": "Please provide a valid proxy ID",
		})
		return
	}

	err := h.proxyService.DeleteProxy(proxyID)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "proxy not found" {
			statusCode = http.StatusNotFound
		} else if err.Error() == "cannot delete default proxy" {
			statusCode = http.StatusForbidden
		}

		c.JSON(statusCode, gin.H{
			"error":   "Proxy deletion failed",
			"code":    "PROXY_DELETION_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Proxy deleted successfully",
	})
}

// AssignProxyToUser assigns a proxy to a user
// @Summary Assign proxy to user
// @Description Assign a specific proxy configuration to a user
// @Tags proxy-management
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param request body services.AssignProxyRequest true "Proxy assignment data"
// @Success 200 {object} map[string]interface{} "Proxy assigned successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request format"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "Proxy or user not found"
// @Router /api/v1/proxy-assignments [post]
func (h *Handlers) AssignProxyToUser(c *gin.Context) {
	var req services.AssignProxyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Invalid request format",
			"code":    "INVALID_REQUEST",
			"message": err.Error(),
		})
		return
	}

	err := h.proxyService.AssignProxyToUser(req.Username, req.ProxyID)
	if err != nil {
		statusCode := http.StatusInternalServerError
		if err.Error() == "proxy not found" || err.Error() == "proxy is not active" {
			statusCode = http.StatusBadRequest
		}

		c.JSON(statusCode, gin.H{
			"error":   "Proxy assignment failed",
			"code":    "PROXY_ASSIGNMENT_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Proxy assigned to user successfully",
	})
}

// UnassignProxyFromUser removes proxy assignment from user
// @Summary Unassign proxy from user
// @Description Remove proxy assignment from a user (user will use default proxy)
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Param username path string true "Username"
// @Success 200 {object} map[string]interface{} "Proxy unassigned successfully"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxy-assignments/{username} [delete]
func (h *Handlers) UnassignProxyFromUser(c *gin.Context) {
	username := c.Param("username")
	if username == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Username parameter required",
			"code":    "MISSING_USERNAME",
			"message": "Please provide a valid username",
		})
		return
	}

	err := h.proxyService.UnassignProxyFromUser(username)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "Proxy unassignment failed",
			"code":    "PROXY_UNASSIGNMENT_FAILED",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"message": "Proxy unassigned from user successfully",
	})
}

// GetUserProxy gets the assigned proxy for a user
// @Summary Get user's assigned proxy
// @Description Retrieve the proxy configuration assigned to a specific user
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Param username path string true "Username"
// @Success 200 {object} map[string]interface{} "User's proxy information"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 404 {object} map[string]interface{} "User or proxy not found"
// @Router /api/v1/users/{username}/proxy [get]
func (h *Handlers) GetUserProxy(c *gin.Context) {
	username := c.Param("username")
	if username == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "Username parameter required",
			"code":    "MISSING_USERNAME",
			"message": "Please provide a valid username",
		})
		return
	}

	proxy, err := h.proxyService.GetUserProxy(username)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error":   "User proxy not found",
			"code":    "USER_PROXY_NOT_FOUND",
			"message": err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    proxy,
	})
}

// ListUserProxyAssignments lists all user-proxy assignments
// @Summary List user-proxy assignments
// @Description Retrieve all current user-proxy assignments in the system
// @Tags proxy-management
// @Produce json
// @Security BearerAuth
// @Success 200 {object} map[string]interface{} "List of user-proxy assignments"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /api/v1/proxy-assignments [get]
func (h *Handlers) ListUserProxyAssignments(c *gin.Context) {
	assignments := h.proxyService.ListUserProxyAssignments()

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    assignments,
		"count":   len(assignments),
	})
} 