package services

import (
	"sync"
	"time"
)

// AnalyticsService handles analytics and metrics
type AnalyticsService struct {
	mu      sync.RWMutex
	metrics *Metrics
}

// Metrics holds analytics data
type Metrics struct {
	TotalRequests     int64     `json:"total_requests"`
	SuccessfulScrapes int64     `json:"successful_scrapes"`
	FailedScrapes     int64     `json:"failed_scrapes"`
	AverageLatency    float64   `json:"average_latency_ms"`
	LastScrapeTime    time.Time `json:"last_scrape_time"`
	StartTime         time.Time `json:"start_time"`
	ProxyUsage        int64     `json:"proxy_usage_count"`
	TopASINs          []string  `json:"top_asins"`
	ErrorCounts       map[string]int64 `json:"error_counts"`
}

// Event represents an analytics event
type Event struct {
	Type      string                 `json:"type"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	Data      map[string]interface{} `json:"data"`
}

// PerformanceMetrics holds performance data
type PerformanceMetrics struct {
	RequestsPerMinute float64           `json:"requests_per_minute"`
	SuccessRate       float64           `json:"success_rate"`
	AverageLatency    float64           `json:"average_latency_ms"`
	ProxyPerformance  map[string]float64 `json:"proxy_performance"`
	ErrorDistribution map[string]float64 `json:"error_distribution"`
	LastHourStats     *HourlyStats      `json:"last_hour_stats"`
}

// HourlyStats holds hourly statistics
type HourlyStats struct {
	Requests  int64   `json:"requests"`
	Successes int64   `json:"successes"`
	Failures  int64   `json:"failures"`
	AvgTime   float64 `json:"avg_response_time_ms"`
}

// NewAnalyticsService creates a new analytics service
func NewAnalyticsService() *AnalyticsService {
	return &AnalyticsService{
		metrics: &Metrics{
			StartTime:    time.Now(),
			ErrorCounts:  make(map[string]int64),
			TopASINs:     make([]string, 0),
		},
	}
}

// TrackRequest tracks a scraping request
func (s *AnalyticsService) TrackRequest(success bool, latency time.Duration, asin string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.metrics.TotalRequests++
	s.metrics.LastScrapeTime = time.Now()

	if success {
		s.metrics.SuccessfulScrapes++
		if asin != "" {
			s.addToTopASINs(asin)
		}
	} else {
		s.metrics.FailedScrapes++
	}

	// Update average latency (simple moving average)
	currentAvg := s.metrics.AverageLatency
	totalRequests := float64(s.metrics.TotalRequests)
	s.metrics.AverageLatency = (currentAvg*(totalRequests-1) + float64(latency.Milliseconds())) / totalRequests
}

// TrackError tracks an error occurrence
func (s *AnalyticsService) TrackError(errorType string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.metrics.ErrorCounts[errorType]++
}

// TrackProxyUsage tracks proxy usage
func (s *AnalyticsService) TrackProxyUsage() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.metrics.ProxyUsage++
}

// TrackEvent tracks a custom analytics event
func (s *AnalyticsService) TrackEvent(userID, eventType string, data map[string]interface{}) {
	// In a real implementation, you might store these events in a database
	// or send them to an analytics service like Google Analytics or Mixpanel
	event := Event{
		Type:      eventType,
		Timestamp: time.Now(),
		UserID:    userID,
		Data:      data,
	}

	// For now, we'll just log the event (in production, persist this)
	_ = event
}

// GetStats returns current analytics statistics
func (s *AnalyticsService) GetStats() *Metrics {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Return a copy to avoid race conditions
	statsCopy := *s.metrics
	statsCopy.ErrorCounts = make(map[string]int64)
	for k, v := range s.metrics.ErrorCounts {
		statsCopy.ErrorCounts[k] = v
	}

	statsCopy.TopASINs = make([]string, len(s.metrics.TopASINs))
	copy(statsCopy.TopASINs, s.metrics.TopASINs)

	return &statsCopy
}

// GetPerformanceMetrics returns performance metrics
func (s *AnalyticsService) GetPerformanceMetrics() *PerformanceMetrics {
	s.mu.RLock()
	defer s.mu.RUnlock()

	uptime := time.Since(s.metrics.StartTime)
	requestsPerMinute := float64(s.metrics.TotalRequests) / uptime.Minutes()
	
	var successRate float64
	if s.metrics.TotalRequests > 0 {
		successRate = float64(s.metrics.SuccessfulScrapes) / float64(s.metrics.TotalRequests) * 100
	}

	// Calculate error distribution
	errorDistribution := make(map[string]float64)
	totalErrors := s.metrics.FailedScrapes
	if totalErrors > 0 {
		for errorType, count := range s.metrics.ErrorCounts {
			errorDistribution[errorType] = float64(count) / float64(totalErrors) * 100
		}
	}

	return &PerformanceMetrics{
		RequestsPerMinute: requestsPerMinute,
		SuccessRate:       successRate,
		AverageLatency:    s.metrics.AverageLatency,
		ProxyPerformance:  map[string]float64{
			"usage_percentage": float64(s.metrics.ProxyUsage) / float64(s.metrics.TotalRequests) * 100,
		},
		ErrorDistribution: errorDistribution,
		LastHourStats: &HourlyStats{
			Requests:  s.metrics.TotalRequests, // Simplified for this example
			Successes: s.metrics.SuccessfulScrapes,
			Failures:  s.metrics.FailedScrapes,
			AvgTime:   s.metrics.AverageLatency,
		},
	}
}

// ResetStats resets all analytics data
func (s *AnalyticsService) ResetStats() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.metrics = &Metrics{
		StartTime:   time.Now(),
		ErrorCounts: make(map[string]int64),
		TopASINs:    make([]string, 0),
	}
}

// addToTopASINs adds an ASIN to the top ASINs list (simplified implementation)
func (s *AnalyticsService) addToTopASINs(asin string) {
	// Simple implementation - just keep the last 10 unique ASINs
	for i, existingASIN := range s.metrics.TopASINs {
		if existingASIN == asin {
			// Move to front
			s.metrics.TopASINs = append([]string{asin}, append(s.metrics.TopASINs[:i], s.metrics.TopASINs[i+1:]...)...)
			return
		}
	}

	// Add new ASIN to front
	s.metrics.TopASINs = append([]string{asin}, s.metrics.TopASINs...)
	
	// Keep only top 10
	if len(s.metrics.TopASINs) > 10 {
		s.metrics.TopASINs = s.metrics.TopASINs[:10]
	}
} 