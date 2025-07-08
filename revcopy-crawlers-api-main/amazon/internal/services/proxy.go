package services

import (
	"crypto/tls"
	"fmt"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ProxyService handles proxy operations
type ProxyService struct {
	client          *http.Client
	config          ProxyConfig
	proxies         map[string]*ProxyEntry // All available proxies
	userProxies     map[string]string      // User to proxy mapping
	defaultProxyID  string                 // Default proxy ID
	mutex           sync.RWMutex           // Thread safety
}

// ProxyConfig holds proxy configuration
type ProxyConfig struct {
	Username string
	Password string
	Host     string
	Port     string
	Enabled  bool
}

// ProxyEntry represents a stored proxy configuration
type ProxyEntry struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Username    string    `json:"username"`
	Password    string    `json:"-"` // Never expose password in JSON
	Host        string    `json:"host"`
	Port        string    `json:"port"`
	Active      bool      `json:"active"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	CreatedBy   string    `json:"created_by"`
}

// CreateProxyRequest represents proxy creation request
type CreateProxyRequest struct {
	Name     string `json:"name" binding:"required"`
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
	Host     string `json:"host" binding:"required"`
	Port     string `json:"port" binding:"required"`
	Active   bool   `json:"active"`
}

// UpdateProxyRequest represents proxy update request
type UpdateProxyRequest struct {
	Name     string `json:"name,omitempty"`
	Username string `json:"username,omitempty"`
	Password string `json:"password,omitempty"`
	Host     string `json:"host,omitempty"`
	Port     string `json:"port,omitempty"`
	Active   *bool  `json:"active,omitempty"`
}

// ProxyResponse represents proxy response (without sensitive data)
type ProxyResponse struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Username  string    `json:"username"`
	Host      string    `json:"host"`
	Port      string    `json:"port"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	CreatedBy string    `json:"created_by"`
}

// AssignProxyRequest represents user-proxy assignment request
type AssignProxyRequest struct {
	Username string `json:"username" binding:"required"`
	ProxyID  string `json:"proxy_id" binding:"required"`
}

// ProxyStatus represents proxy status information
type ProxyStatus struct {
	Connected bool   `json:"connected"`
	IP        string `json:"ip,omitempty"`
	Location  string `json:"location,omitempty"`
	Latency   int64  `json:"latency_ms"`
	Error     string `json:"error,omitempty"`
}

// NewProxyService creates a new proxy service
func NewProxyService() *ProxyService {
	service := &ProxyService{
		client: &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true,
				},
			},
		},
		config: ProxyConfig{
			Enabled: false,
		},
		proxies:     make(map[string]*ProxyEntry),
		userProxies: make(map[string]string),
	}
	
	// Create default proxy with anvitop credentials
	service.createDefaultProxy()
	
	return service
}

// createDefaultProxy creates the default proxy configuration
func (s *ProxyService) createDefaultProxy() {
	defaultProxy := &ProxyEntry{
		ID:        uuid.New().String(),
		Name:      "Default Anvitop Proxy",
		Username:  "anvitop",
		Password:  "C29UaLSZPx",
		Host:      "74.124.222.120",
		Port:      "50100",
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		CreatedBy: "system",
	}
	
	s.proxies[defaultProxy.ID] = defaultProxy
	s.defaultProxyID = defaultProxy.ID
}

// ConfigureProxy sets up proxy configuration
func (s *ProxyService) ConfigureProxy(username, password, host, port string) error {
	s.config = ProxyConfig{
		Username: username,
		Password: password,
		Host:     host,
		Port:     port,
		Enabled:  true,
	}

	// Create proxy URL
	proxyURL := fmt.Sprintf("http://%s:%s@%s:%s", username, password, host, port)
	
	// Parse proxy URL
	proxy, err := url.Parse(proxyURL)
	if err != nil {
		s.config.Enabled = false
		return fmt.Errorf("invalid proxy configuration: %w", err)
	}

	// Update HTTP client with proxy
	transport := &http.Transport{
		Proxy: http.ProxyURL(proxy),
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true,
		},
	}

	s.client = &http.Client{
		Timeout:   30 * time.Second,
		Transport: transport,
	}

	return nil
}

// GetClient returns the HTTP client (with or without proxy)
func (s *ProxyService) GetClient() *http.Client {
	return s.client
}

// IsProxyEnabled returns whether proxy is enabled
func (s *ProxyService) IsProxyEnabled() bool {
	return s.config.Enabled
}

// GetProxyConfig returns current proxy configuration (without sensitive data)
func (s *ProxyService) GetProxyConfig() map[string]interface{} {
	return map[string]interface{}{
		"enabled":  s.config.Enabled,
		"host":     s.config.Host,
		"port":     s.config.Port,
		"username": s.config.Username,
		// Don't expose password
	}
}

// TestProxy tests the proxy connection
func (s *ProxyService) TestProxy() *ProxyStatus {
	if !s.config.Enabled {
		return &ProxyStatus{
			Connected: false,
			Error:     "Proxy not configured",
		}
	}

	start := time.Now()
	
	// Test connection by making a request to a test endpoint
	resp, err := s.client.Get("https://httpbin.org/ip")
	latency := time.Since(start).Milliseconds()

	if err != nil {
		return &ProxyStatus{
			Connected: false,
			Latency:   latency,
			Error:     err.Error(),
		}
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return &ProxyStatus{
			Connected: false,
			Latency:   latency,
			Error:     fmt.Sprintf("HTTP %d", resp.StatusCode),
		}
	}

	return &ProxyStatus{
		Connected: true,
		Latency:   latency,
		IP:        "Proxy IP (hidden for security)",
		Location:  "Proxy Location",
	}
}

// DisableProxy disables proxy usage
func (s *ProxyService) DisableProxy() {
	s.config.Enabled = false
	
	// Reset client to default (no proxy)
	s.client = &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true,
			},
		},
	}
}

// CreateProxy creates a new proxy configuration
func (s *ProxyService) CreateProxy(req CreateProxyRequest, createdBy string) (*ProxyResponse, error) {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	// Create new proxy
	proxy := &ProxyEntry{
		ID:        uuid.New().String(),
		Name:      req.Name,
		Username:  req.Username,
		Password:  req.Password,
		Host:      req.Host,
		Port:      req.Port,
		Active:    req.Active,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		CreatedBy: createdBy,
	}
	
	s.proxies[proxy.ID] = proxy
	
	return &ProxyResponse{
		ID:        proxy.ID,
		Name:      proxy.Name,
		Username:  proxy.Username,
		Host:      proxy.Host,
		Port:      proxy.Port,
		Active:    proxy.Active,
		CreatedAt: proxy.CreatedAt,
		UpdatedAt: proxy.UpdatedAt,
		CreatedBy: proxy.CreatedBy,
	}, nil
}

// GetProxy gets a proxy by ID
func (s *ProxyService) GetProxy(proxyID string) (*ProxyResponse, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	proxy, exists := s.proxies[proxyID]
	if !exists {
		return nil, fmt.Errorf("proxy not found")
	}
	
	return &ProxyResponse{
		ID:        proxy.ID,
		Name:      proxy.Name,
		Username:  proxy.Username,
		Host:      proxy.Host,
		Port:      proxy.Port,
		Active:    proxy.Active,
		CreatedAt: proxy.CreatedAt,
		UpdatedAt: proxy.UpdatedAt,
		CreatedBy: proxy.CreatedBy,
	}, nil
}

// ListProxies lists all proxy configurations
func (s *ProxyService) ListProxies() []*ProxyResponse {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	var proxies []*ProxyResponse
	
	for _, proxy := range s.proxies {
		proxies = append(proxies, &ProxyResponse{
			ID:        proxy.ID,
			Name:      proxy.Name,
			Username:  proxy.Username,
			Host:      proxy.Host,
			Port:      proxy.Port,
			Active:    proxy.Active,
			CreatedAt: proxy.CreatedAt,
			UpdatedAt: proxy.UpdatedAt,
			CreatedBy: proxy.CreatedBy,
		})
	}
	
	return proxies
}

// UpdateProxy updates an existing proxy
func (s *ProxyService) UpdateProxy(proxyID string, req UpdateProxyRequest) (*ProxyResponse, error) {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	proxy, exists := s.proxies[proxyID]
	if !exists {
		return nil, fmt.Errorf("proxy not found")
	}
	
	// Update fields if provided
	if req.Name != "" {
		proxy.Name = req.Name
	}
	if req.Username != "" {
		proxy.Username = req.Username
	}
	if req.Password != "" {
		proxy.Password = req.Password
	}
	if req.Host != "" {
		proxy.Host = req.Host
	}
	if req.Port != "" {
		proxy.Port = req.Port
	}
	if req.Active != nil {
		proxy.Active = *req.Active
	}
	
	proxy.UpdatedAt = time.Now()
	
	return &ProxyResponse{
		ID:        proxy.ID,
		Name:      proxy.Name,
		Username:  proxy.Username,
		Host:      proxy.Host,
		Port:      proxy.Port,
		Active:    proxy.Active,
		CreatedAt: proxy.CreatedAt,
		UpdatedAt: proxy.UpdatedAt,
		CreatedBy: proxy.CreatedBy,
	}, nil
}

// DeleteProxy deletes a proxy configuration
func (s *ProxyService) DeleteProxy(proxyID string) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	if _, exists := s.proxies[proxyID]; !exists {
		return fmt.Errorf("proxy not found")
	}
	
	// Don't allow deleting default proxy
	if proxyID == s.defaultProxyID {
		return fmt.Errorf("cannot delete default proxy")
	}
	
	// Remove proxy assignments
	for username, assignedProxyID := range s.userProxies {
		if assignedProxyID == proxyID {
			delete(s.userProxies, username)
		}
	}
	
	delete(s.proxies, proxyID)
	return nil
}

// AssignProxyToUser assigns a proxy to a user
func (s *ProxyService) AssignProxyToUser(username, proxyID string) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	// Check if proxy exists and is active
	proxy, exists := s.proxies[proxyID]
	if !exists {
		return fmt.Errorf("proxy not found")
	}
	
	if !proxy.Active {
		return fmt.Errorf("proxy is not active")
	}
	
	s.userProxies[username] = proxyID
	return nil
}

// UnassignProxyFromUser removes proxy assignment from user
func (s *ProxyService) UnassignProxyFromUser(username string) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()
	
	delete(s.userProxies, username)
	return nil
}

// GetUserProxy gets the assigned proxy for a user
func (s *ProxyService) GetUserProxy(username string) (*ProxyResponse, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	proxyID, exists := s.userProxies[username]
	if !exists {
		// Return default proxy if no specific assignment
		proxyID = s.defaultProxyID
	}
	
	proxy, exists := s.proxies[proxyID]
	if !exists {
		return nil, fmt.Errorf("assigned proxy not found")
	}
	
	return &ProxyResponse{
		ID:        proxy.ID,
		Name:      proxy.Name,
		Username:  proxy.Username,
		Host:      proxy.Host,
		Port:      proxy.Port,
		Active:    proxy.Active,
		CreatedAt: proxy.CreatedAt,
		UpdatedAt: proxy.UpdatedAt,
		CreatedBy: proxy.CreatedBy,
	}, nil
}

// GetClientForUser returns HTTP client configured with user's assigned proxy
func (s *ProxyService) GetClientForUser(username string) *http.Client {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	proxyID, exists := s.userProxies[username]
	if !exists {
		proxyID = s.defaultProxyID
	}
	
	proxy, exists := s.proxies[proxyID]
	if !exists || !proxy.Active {
		// Return default client if no proxy or proxy inactive
		return &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true,
				},
			},
		}
	}
	
	// Create proxy URL
	proxyURL := fmt.Sprintf("http://%s:%s@%s:%s", proxy.Username, proxy.Password, proxy.Host, proxy.Port)
	
	// Parse proxy URL
	parsedProxy, err := url.Parse(proxyURL)
	if err != nil {
		// Return default client if proxy URL is invalid
		return &http.Client{
			Timeout: 30 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true,
				},
			},
		}
	}
	
	// Return client with proxy
	return &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			Proxy: http.ProxyURL(parsedProxy),
			TLSClientConfig: &tls.Config{
				InsecureSkipVerify: true,
			},
		},
	}
}

// ListUserProxyAssignments lists all user-proxy assignments
func (s *ProxyService) ListUserProxyAssignments() map[string]*ProxyResponse {
	s.mutex.RLock()
	defer s.mutex.RUnlock()
	
	assignments := make(map[string]*ProxyResponse)
	
	for username, proxyID := range s.userProxies {
		if proxy, exists := s.proxies[proxyID]; exists {
			assignments[username] = &ProxyResponse{
				ID:        proxy.ID,
				Name:      proxy.Name,
				Username:  proxy.Username,
				Host:      proxy.Host,
				Port:      proxy.Port,
				Active:    proxy.Active,
				CreatedAt: proxy.CreatedAt,
				UpdatedAt: proxy.UpdatedAt,
				CreatedBy: proxy.CreatedBy,
			}
		}
	}
	
	return assignments
} 