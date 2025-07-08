package services

import (
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/PuerkitoBio/goquery"
)

// ScraperService handles Amazon scraping operations
type ScraperService struct {
	proxyService *ProxyService
}

// AmazonProduct represents a scraped Amazon product
type AmazonProduct struct {
	ASIN        string   `json:"asin"`
	Title       string   `json:"title"`
	Price       float64  `json:"price"`
	Currency    string   `json:"currency"`
	Rating      float64  `json:"rating"`
	ReviewCount int      `json:"review_count"`
	Images      []string `json:"images"`
	Description string   `json:"description"`
	Availability string   `json:"availability"`
	Brand       string   `json:"brand"`
	Category    string   `json:"category"`
	URL         string   `json:"url"`
	ScrapedAt   string   `json:"scraped_at"`
}

// ScrapeRequest represents a scraping request
type ScrapeRequest struct {
	URL    string `json:"url" binding:"required"`
	ASIN   string `json:"asin,omitempty"`
	Region string `json:"region,omitempty"`
}

// BulkScrapeRequest represents bulk scraping request
type BulkScrapeRequest struct {
	URLs   []string `json:"urls" binding:"required"`
	ASINs  []string `json:"asins,omitempty"`
	Region string   `json:"region,omitempty"`
}

// SearchRequest represents product search request
type SearchRequest struct {
	Query    string `json:"query" binding:"required"`
	Category string `json:"category,omitempty"`
	MinPrice int    `json:"min_price,omitempty"`
	MaxPrice int    `json:"max_price,omitempty"`
	Rating   int    `json:"min_rating,omitempty"`
	Page     int    `json:"page,omitempty"`
}

// NewScraperService creates a new scraper service
func NewScraperService(proxyService *ProxyService) *ScraperService {
	return &ScraperService{
		proxyService: proxyService,
	}
}

// ScrapeProduct scrapes a single Amazon product
func (s *ScraperService) ScrapeProduct(url string) (*AmazonProduct, error) {
	client := s.proxyService.GetClient()
	
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	// Set realistic headers to avoid detection
	s.setHeaders(req)

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch product page: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	return s.parseProductPage(string(body), url)
}

// BulkScrapeProducts scrapes multiple Amazon products
func (s *ScraperService) BulkScrapeProducts(urls []string) ([]*AmazonProduct, error) {
	var products []*AmazonProduct
	var errors []string

	for i, url := range urls {
		// Add delay between requests to avoid rate limiting
		if i > 0 {
			time.Sleep(2 * time.Second)
		}

		product, err := s.ScrapeProduct(url)
		if err != nil {
			errors = append(errors, fmt.Sprintf("URL %s: %v", url, err))
			continue
		}

		products = append(products, product)
	}

	if len(errors) > 0 && len(products) == 0 {
		return nil, fmt.Errorf("all requests failed: %s", strings.Join(errors, "; "))
	}

	return products, nil
}

// SearchProducts searches Amazon for products
func (s *ScraperService) SearchProducts(query string, page int) ([]*AmazonProduct, error) {
	searchURL := fmt.Sprintf("https://www.amazon.com/s?k=%s&page=%d", 
		strings.ReplaceAll(query, " ", "+"), page)

	client := s.proxyService.GetClient()
	
	req, err := http.NewRequest("GET", searchURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create search request: %w", err)
	}

	s.setHeaders(req)

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch search results: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("search request failed with status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read search response: %w", err)
	}

	return s.parseSearchResults(string(body))
}

// parseProductPage parses Amazon product page HTML
func (s *ScraperService) parseProductPage(html, url string) (*AmazonProduct, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	product := &AmazonProduct{
		URL:       url,
		ScrapedAt: time.Now().UTC().Format(time.RFC3339),
	}

	// Extract ASIN from URL
	asinRegex := regexp.MustCompile(`/dp/([A-Z0-9]{10})`)
	if matches := asinRegex.FindStringSubmatch(url); len(matches) > 1 {
		product.ASIN = matches[1]
	}

	// Extract title
	product.Title = doc.Find("#productTitle").Text()
	product.Title = strings.TrimSpace(product.Title)

	// Extract price
	priceText := doc.Find(".a-price-whole").First().Text()
	if priceText == "" {
		priceText = doc.Find(".a-price .a-offscreen").First().Text()
	}
	if price, err := s.parsePrice(priceText); err == nil {
		product.Price = price
	}

	// Extract currency
	product.Currency = "USD" // Default, could be extracted from price symbol

	// Extract rating
	ratingText := doc.Find(".a-icon-alt").First().Text()
	if rating, err := s.parseRating(ratingText); err == nil {
		product.Rating = rating
	}

	// Extract review count
	reviewText := doc.Find("#acrCustomerReviewText").Text()
	if count, err := s.parseReviewCount(reviewText); err == nil {
		product.ReviewCount = count
	}

	// Extract images
	doc.Find("#landingImage").Each(func(i int, sel *goquery.Selection) {
		if src, exists := sel.Attr("src"); exists {
			product.Images = append(product.Images, src)
		}
	})

	// Extract description
	product.Description = doc.Find("#feature-bullets ul").Text()
	product.Description = strings.TrimSpace(product.Description)

	// Extract availability
	product.Availability = doc.Find("#availability span").Text()
	product.Availability = strings.TrimSpace(product.Availability)

	// Extract brand
	product.Brand = doc.Find("#bylineInfo").Text()
	product.Brand = strings.TrimSpace(product.Brand)

	return product, nil
}

// parseSearchResults parses Amazon search results
func (s *ScraperService) parseSearchResults(html string) ([]*AmazonProduct, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, fmt.Errorf("failed to parse search HTML: %w", err)
	}

	var products []*AmazonProduct

	doc.Find("[data-component-type='s-search-result']").Each(func(i int, sel *goquery.Selection) {
		product := &AmazonProduct{
			ScrapedAt: time.Now().UTC().Format(time.RFC3339),
		}

		// Extract ASIN
		if asin, exists := sel.Attr("data-asin"); exists {
			product.ASIN = asin
		}

		// Extract title
		titleEl := sel.Find("h2 a span")
		product.Title = strings.TrimSpace(titleEl.Text())

		// Extract URL
		if href, exists := sel.Find("h2 a").Attr("href"); exists {
			product.URL = "https://www.amazon.com" + href
		}

		// Extract price
		priceText := sel.Find(".a-price .a-offscreen").First().Text()
		if price, err := s.parsePrice(priceText); err == nil {
			product.Price = price
		}

		// Extract rating
		ratingText := sel.Find(".a-icon-alt").First().Text()
		if rating, err := s.parseRating(ratingText); err == nil {
			product.Rating = rating
		}

		// Extract image
		if imgSrc, exists := sel.Find("img").Attr("src"); exists {
			product.Images = []string{imgSrc}
		}

		if product.ASIN != "" && product.Title != "" {
			products = append(products, product)
		}
	})

	return products, nil
}

// Helper methods
func (s *ScraperService) setHeaders(req *http.Request) {
	req.Header.Set("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.5")
	req.Header.Set("Accept-Encoding", "gzip, deflate")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")
}

func (s *ScraperService) parsePrice(priceText string) (float64, error) {
	re := regexp.MustCompile(`[\d,]+\.?\d*`)
	match := re.FindString(priceText)
	if match == "" {
		return 0, fmt.Errorf("no price found")
	}
	match = strings.ReplaceAll(match, ",", "")
	return strconv.ParseFloat(match, 64)
}

func (s *ScraperService) parseRating(ratingText string) (float64, error) {
	re := regexp.MustCompile(`(\d+\.?\d*) out of`)
	matches := re.FindStringSubmatch(ratingText)
	if len(matches) < 2 {
		return 0, fmt.Errorf("no rating found")
	}
	return strconv.ParseFloat(matches[1], 64)
}

func (s *ScraperService) parseReviewCount(reviewText string) (int, error) {
	re := regexp.MustCompile(`([\d,]+) ratings`)
	matches := re.FindStringSubmatch(reviewText)
	if len(matches) < 2 {
		return 0, fmt.Errorf("no review count found")
	}
	countStr := strings.ReplaceAll(matches[1], ",", "")
	return strconv.Atoi(countStr)
} 