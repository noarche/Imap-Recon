package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/emersion/go-imap"
	"github.com/emersion/go-imap/client"
	"gopkg.in/ini.v1"
)

// ANSI color codes
const (
	Reset   = "\033[0m"
	Red     = "\033[31m"
	Green   = "\033[32m"
	Yellow  = "\033[33m"
	Blue    = "\033[34m"
	Magenta = "\033[35m"
	Cyan    = "\033[36m"
	Bold    = "\033[1m"
)

type EmailAccount struct {
	Email    string
	IMAPHost string
	SMTPHost string
	Username string
	Password string
}

var accounts []EmailAccount
var emailList []*imap.Message
var downloadMode bool

func loadConfig(configFile string) {
	cfg, err := ini.Load(configFile)
	if err != nil {
		log.Fatalf(Red+"Failed to read config file: %v"+Reset, err)
	}

	for _, section := range cfg.Sections() {
		if section.Name() == "DEFAULT" {
			continue
		}
		accounts = append(accounts, EmailAccount{
			Email:    section.Key("email").String(),
			IMAPHost: section.Key("imap_host").String(),
			SMTPHost: section.Key("smtp_host").String(),
			Username: section.Key("username").String(),
			Password: section.Key("password").String(),
		})
	}
}

func listMailboxes(account EmailAccount) ([]string, error) {
	c, err := client.DialTLS(account.IMAPHost, nil)
	if err != nil {
		return nil, err
	}
	defer c.Logout()

	if err := c.Login(account.Username, account.Password); err != nil {
		return nil, err
	}

	mailboxes := make(chan *imap.MailboxInfo, 10)
	done := make(chan error, 1)

	go func() {
		done <- c.List("", "*", mailboxes)
	}()

	var mailboxNames []string
	for m := range mailboxes {
		mailboxNames = append(mailboxNames, m.Name)
	}

	if err := <-done; err != nil {
		return nil, err
	}
	return mailboxNames, nil
}

func promptUserForConfig() string {
	files, err := os.ReadDir("./configs/")
	if err != nil {
		log.Fatalf(Red+"Failed to read configs directory: %v"+Reset, err)
	}

	if len(files) == 0 {
		log.Fatalf(Red + "No configuration files found in './configs/' directory." + Reset)
	}

	pageSize := 9000
	totalFiles := len(files)
	page := 0

	for {
		start := page * pageSize
		end := start + pageSize
		if end > totalFiles {
			end = totalFiles
		}

		fmt.Println(Bold + Cyan + "Available Configurations:" + Reset)
		for i := start; i < end; i++ {
			if !files[i].IsDir() && strings.HasSuffix(files[i].Name(), ".ini") {
				fmt.Printf("[%d] %s\n", i+1, files[i].Name())
			}
		}

		if end < totalFiles {
			fmt.Println(Bold + Yellow + "[n] Next page" + Reset)
		}
		if page > 0 {
			fmt.Println(Bold + Yellow + "[p] Previous page" + Reset)
		}

		fmt.Println(Bold + Yellow + "[q] Quit" + Reset)

		var input string
		fmt.Print(Bold + Magenta + "Select a configuration file by number or navigate: " + Reset)
		fmt.Scan(&input)

		if input == "n" && end < totalFiles {
			page++
			continue
		} else if input == "p" && page > 0 {
			page--
			continue
		} else if input == "q" {
			log.Fatalf(Red + "User exited configuration selection." + Reset)
		}

		choice, err := strconv.Atoi(input)
		if err != nil || choice < 1 || choice > totalFiles {
			fmt.Println(Red + "Invalid choice. Please try again." + Reset)
			continue
		}

		return filepath.Join("./configs/", files[choice-1].Name())
	}
}

func fetchEmails(emailAccount EmailAccount, folder string) ([]*imap.Message, error) {
	c, err := client.DialTLS(emailAccount.IMAPHost, nil)
	if err != nil {
		return nil, err
	}
	defer c.Logout()

	if err := c.Login(emailAccount.Username, emailAccount.Password); err != nil {
		return nil, err
	}

	mbox, err := c.Select(folder, false) // <- use passed-in folder
	if err != nil {
		return nil, err
	}

	if mbox.Messages == 0 {
		log.Println(Yellow + "No emails in inbox." + Reset)
		return nil, nil
	}

	seqset := new(imap.SeqSet)
	seqset.AddRange(1, mbox.Messages)

	messages := make(chan *imap.Message, 10)
	go func() {
		if err := c.Fetch(seqset, []imap.FetchItem{imap.FetchEnvelope}, messages); err != nil {
			log.Println(Red+"Fetch error:"+Reset, err)
		}
	}()

	var fetchedEmails []*imap.Message
	for msg := range messages {
		if msg == nil || msg.Envelope == nil {
			log.Println(Red + "Skipping an invalid email." + Reset)
			continue
		}
		fetchedEmails = append(fetchedEmails, msg)
	}
	return fetchedEmails, nil
}

func saveEmailAsHTML(searchTerm, configName, accountEmail string, msg *imap.Message) {
	if msg == nil || msg.Envelope == nil {
		return
	}

	timestamp := msg.Envelope.Date.Format("2006-01-02_15-04-05")
	sender := "Unknown_Sender"
	if len(msg.Envelope.From) > 0 && msg.Envelope.From[0] != nil {
		sender = strings.ReplaceAll(msg.Envelope.From[0].Address(), " ", "_")
	}
	subject := strings.ReplaceAll(msg.Envelope.Subject, " ", "_")
	subject = strings.ReplaceAll(subject, "/", "_") // Avoid invalid file paths

	// Corrected directory structure: ./results/{keyword}/{ConfigName}/{emailaddress}
	dirPath := filepath.Join("results", searchTerm, configName, accountEmail)
	if err := os.MkdirAll(dirPath, os.ModePerm); err != nil {
		log.Println(Red+"Failed to create directory:"+Reset, err)
		return
	}

	filePath := filepath.Join(dirPath, fmt.Sprintf("%s_%s_%s.html", timestamp, sender, subject))
	file, err := os.Create(filePath)
	if err != nil {
		log.Println(Red+"Failed to create file:"+Reset, err)
		return
	}
	defer file.Close()

	// Write a simple HTML representation of the email
	htmlContent := fmt.Sprintf("<html><body><h1>Subject: %s</h1><h2>From: %s</h2><h3>Date: %s</h3></body></html>",
		msg.Envelope.Subject, sender, timestamp)
	_, err = file.WriteString(htmlContent)
	if err != nil {
		log.Println(Red+"Failed to write to file:"+Reset, err)
	}
}

func displayEmails() {
	if len(emailList) == 0 {
		fmt.Println(Red + "No emails to display." + Reset)
		return
	}

	fmt.Println(Bold + Cyan + "Fetched Emails:" + Reset)
	for _, msg := range emailList {
		if msg == nil || msg.Envelope == nil {
			fmt.Println(Red + "Skipping an invalid email entry." + Reset)
			continue
		}

		// Ensure there is at least one sender before accessing From[0]
		sender := "Unknown Sender"
		if len(msg.Envelope.From) > 0 && msg.Envelope.From[0] != nil {
			sender = msg.Envelope.From[0].Address()
		}

		timestamp := msg.Envelope.Date.Format("2006-01-02 15:04:05")
		fmt.Printf(Bold+Yellow+"[%s] "+Reset+"From: "+Green+"%s"+Reset+" | Subject: "+Blue+"%s"+Reset+"\n",
			timestamp, sender, msg.Envelope.Subject)
	}
}

func handleUserInput(configName string) {
	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print(Bold + Magenta + "Enter search term or command: " + Reset)
		scanner.Scan()
		input := strings.TrimSpace(scanner.Text())

		switch {
		case input == "":
			fmt.Println(Yellow + "Please enter a valid command or search term." + Reset)
			continue

		case input == "exit":
			fmt.Println(Red + "Exiting..." + Reset)
			return

		case input == "refresh":
			emailList = nil
			for _, account := range accounts {
				fmt.Println(Bold + "Fetching emails for: " + Cyan + account.Email + Reset)
				emails, err := fetchEmails(account, "INBOX")
				if err != nil {
					log.Println(Red+"Error fetching emails:"+Reset, err)
					continue
				}
				emailList = append(emailList, emails...)
			}
			displayEmails()

		case input == "sent":
			fmt.Println(Yellow + "Searching for Sent folder..." + Reset)
			emailList = nil
			for _, account := range accounts {
				folders, err := listMailboxes(account)
				if err != nil {
					log.Println(Red+"Error listing mailboxes:"+Reset, err)
					continue
				}

				// Try to detect the correct "Sent" folder
				var sentFolder string
				for _, folder := range folders {
					lower := strings.ToLower(folder)
					if strings.Contains(lower, "sent") {
						sentFolder = folder
						break
					}
				}

				if sentFolder == "" {
					log.Println(Red + "No 'Sent' folder found for account: " + account.Email + Reset)
					continue
				}

				fmt.Println(Bold + "Fetching emails from: " + Cyan + sentFolder + Reset)
				emails, err := fetchEmails(account, sentFolder)
				if err != nil {
					log.Println(Red+"Error fetching sent emails:"+Reset, err)
					continue
				}
				emailList = append(emailList, emails...)
			}
			displayEmails()

		case strings.Contains(input, "@"):
			// Assume input is an email sender search
			fmt.Println(Yellow + "Searching for sender: " + input + Reset)
			found := false
			for _, msg := range emailList {
				if msg != nil && msg.Envelope != nil && len(msg.Envelope.From) > 0 &&
					msg.Envelope.From[0] != nil &&
					strings.Contains(strings.ToLower(msg.Envelope.From[0].Address()), strings.ToLower(input)) {
					timestamp := msg.Envelope.Date.Format("2006-01-02 15:04:05")
					fmt.Printf(Bold+Yellow+"[%s] "+Reset+"From: "+Green+"%s"+Reset+" | Subject: "+Blue+"%s"+Reset+"\n",
						timestamp, msg.Envelope.From[0].Address(), msg.Envelope.Subject)
					if downloadMode {
						saveEmailAsHTML(input, configName, msg.Envelope.From[0].Address(), msg)
					}
					found = true
				}
			}
			if !found {
				fmt.Println(Red + "No emails from the specified sender found." + Reset)
			}

		default:
			// Assume input is a keyword search
			fmt.Println(Yellow + "Searching for keyword: " + input + Reset)
			found := false
			for _, msg := range emailList {
				if msg != nil && msg.Envelope != nil && strings.Contains(strings.ToLower(msg.Envelope.Subject), strings.ToLower(input)) {
					timestamp := msg.Envelope.Date.Format("2006-01-02 15:04:05")
					sender := "Unknown Sender"
					if len(msg.Envelope.From) > 0 && msg.Envelope.From[0] != nil {
						sender = msg.Envelope.From[0].Address()
					}
					fmt.Printf(Bold+Yellow+"[%s] "+Reset+"From: "+Green+"%s"+Reset+" | Subject: "+Blue+"%s"+Reset+"\n",
						timestamp, sender, msg.Envelope.Subject)
					if downloadMode {
						saveEmailAsHTML(input, configName, sender, msg)
					}
					found = true
				}
			}
			if !found {
				fmt.Println(Red + "No emails matching the keyword found." + Reset)
			}
		}
	}
}

func main() {
	if len(os.Args) > 1 && os.Args[1] == "-dl" {
		downloadMode = true
		fmt.Println(Yellow + "Download mode enabled. Emails will be saved as HTML files." + Reset)
	}

	configFile := promptUserForConfig()
	loadConfig(configFile)

	// Use the base name of the config file (e.g., "account1.ini")
	configName := strings.TrimSuffix(filepath.Base(configFile), filepath.Ext(configFile))

	for _, account := range accounts {
		fmt.Println(Bold + "Fetching emails for: " + Cyan + account.Email + Reset)
		emails, err := fetchEmails(account, "INBOX")
		if err != nil {
			log.Println(Red+"Error fetching emails:"+Reset, err)
			continue
		}
		emailList = append(emailList, emails...)
	}
	displayEmails()
	handleUserInput(configName)
}
