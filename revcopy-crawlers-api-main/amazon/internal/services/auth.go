package services

import (
	"errors"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

// AuthService handles authentication operations
type AuthService struct {
	jwtSecret []byte
	users     map[string]*User // In-memory user storage (use database in production)
}

// Claims represents JWT claims
type Claims struct {
	UserID   string `json:"user_id"`
	Username string `json:"username"`
	jwt.RegisteredClaims
}

// LoginRequest represents login request payload
type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

// LoginResponse represents login response
type LoginResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int64  `json:"expires_in"`
	TokenType    string `json:"token_type"`
}

// User represents a user in the system
type User struct {
	ID        string    `json:"id"`
	Username  string    `json:"username"`
	Password  string    `json:"-"` // Never expose password in JSON
	Role      string    `json:"role"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// CreateUserRequest represents user creation request
type CreateUserRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
	Role     string `json:"role" binding:"required"`
	Active   bool   `json:"active"`
}

// UpdateUserRequest represents user update request
type UpdateUserRequest struct {
	Password string `json:"password,omitempty"`
	Role     string `json:"role,omitempty"`
	Active   *bool  `json:"active,omitempty"`
}

// UserResponse represents user response (without sensitive data)
type UserResponse struct {
	ID        string    `json:"id"`
	Username  string    `json:"username"`
	Role      string    `json:"role"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// NewAuthService creates a new auth service
func NewAuthService(jwtSecret string) *AuthService {
	service := &AuthService{
		jwtSecret: []byte(jwtSecret),
		users:     make(map[string]*User),
	}
	
	// Create default users
	service.createDefaultUsers()
	
	return service
}

// createDefaultUsers creates the default system users
func (s *AuthService) createDefaultUsers() {
	defaultUsers := []User{
		{
			ID:        uuid.New().String(),
			Username:  "admin",
			Password:  "admin123",
			Role:      "admin",
			Active:    true,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
		{
			ID:        uuid.New().String(),
			Username:  "crawler",
			Password:  "crawler123",
			Role:      "crawler",
			Active:    true,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
		{
			ID:        uuid.New().String(),
			Username:  "analytics",
			Password:  "analytics123",
			Role:      "analytics",
			Active:    true,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		},
	}
	
	for _, user := range defaultUsers {
		s.users[user.Username] = &user
	}
}

// Login authenticates user and returns JWT tokens
func (s *AuthService) Login(username, password string) (*LoginResponse, error) {
	// In a real implementation, you would validate credentials against a database
	// For this example, we'll use a simple hardcoded check
	if !s.validateCredentials(username, password) {
		return nil, errors.New("invalid credentials")
	}

	userID := uuid.New().String()
	
	// Generate access token (1 hour expiry)
	accessToken, err := s.generateToken(userID, username, time.Hour)
	if err != nil {
		return nil, err
	}

	// Generate refresh token (7 days expiry)
	refreshToken, err := s.generateToken(userID, username, 7*24*time.Hour)
	if err != nil {
		return nil, err
	}

	return &LoginResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    3600, // 1 hour in seconds
		TokenType:    "Bearer",
	}, nil
}

// ValidateToken validates a JWT token and returns claims
func (s *AuthService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		return s.jwtSecret, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("invalid token")
}

// RefreshToken generates a new access token from a refresh token
func (s *AuthService) RefreshToken(refreshTokenString string) (*LoginResponse, error) {
	claims, err := s.ValidateToken(refreshTokenString)
	if err != nil {
		return nil, errors.New("invalid refresh token")
	}

	// Generate new access token
	accessToken, err := s.generateToken(claims.UserID, claims.Username, time.Hour)
	if err != nil {
		return nil, err
	}

	return &LoginResponse{
		AccessToken: accessToken,
		ExpiresIn:   3600,
		TokenType:   "Bearer",
	}, nil
}

// generateToken generates a JWT token
func (s *AuthService) generateToken(userID, username string, expiry time.Duration) (string, error) {
	claims := Claims{
		UserID:   userID,
		Username: username,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(expiry)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			NotBefore: jwt.NewNumericDate(time.Now()),
			Issuer:    "amazon-crawler",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.jwtSecret)
}

// validateCredentials validates user credentials
func (s *AuthService) validateCredentials(username, password string) bool {
	user, exists := s.users[username]
	if !exists || !user.Active {
		return false
	}
	
	return user.Password == password
}

// CreateUser creates a new user
func (s *AuthService) CreateUser(req CreateUserRequest) (*UserResponse, error) {
	// Check if user already exists
	if _, exists := s.users[req.Username]; exists {
		return nil, errors.New("user already exists")
	}
	
	// Validate role
	validRoles := map[string]bool{
		"admin":     true,
		"crawler":   true,
		"analytics": true,
		"user":      true,
	}
	
	if !validRoles[req.Role] {
		return nil, errors.New("invalid role")
	}
	
	// Create new user
	user := &User{
		ID:        uuid.New().String(),
		Username:  req.Username,
		Password:  req.Password, // In production, hash this password
		Role:      req.Role,
		Active:    req.Active,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	s.users[req.Username] = user
	
	return &UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}, nil
}

// GetUser gets a user by username
func (s *AuthService) GetUser(username string) (*UserResponse, error) {
	user, exists := s.users[username]
	if !exists {
		return nil, errors.New("user not found")
	}
	
	return &UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}, nil
}

// ListUsers lists all users
func (s *AuthService) ListUsers() []*UserResponse {
	var users []*UserResponse
	
	for _, user := range s.users {
		users = append(users, &UserResponse{
			ID:        user.ID,
			Username:  user.Username,
			Role:      user.Role,
			Active:    user.Active,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
		})
	}
	
	return users
}

// UpdateUser updates an existing user
func (s *AuthService) UpdateUser(username string, req UpdateUserRequest) (*UserResponse, error) {
	user, exists := s.users[username]
	if !exists {
		return nil, errors.New("user not found")
	}
	
	// Update fields if provided
	if req.Password != "" {
		user.Password = req.Password // In production, hash this password
	}
	
	if req.Role != "" {
		validRoles := map[string]bool{
			"admin":     true,
			"crawler":   true,
			"analytics": true,
			"user":      true,
		}
		
		if !validRoles[req.Role] {
			return nil, errors.New("invalid role")
		}
		user.Role = req.Role
	}
	
	if req.Active != nil {
		user.Active = *req.Active
	}
	
	user.UpdatedAt = time.Now()
	
	return &UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt,
		UpdatedAt: user.UpdatedAt,
	}, nil
}

// DeleteUser deletes a user
func (s *AuthService) DeleteUser(username string) error {
	if _, exists := s.users[username]; !exists {
		return errors.New("user not found")
	}
	
	// Don't allow deleting admin user
	if username == "admin" {
		return errors.New("cannot delete admin user")
	}
	
	delete(s.users, username)
	return nil
} 