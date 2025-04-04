IMAP Email Parser is a Python script that connects to multiple email accounts via IMAP, searches for emails based on given criteria, and either saves or deletes them. The script supports searching by sender, keyword, and sender with automatic deletion. It also includes SOCKS5 proxy support for privacy.
Features

    Connects to multiple email accounts using credentials from a config file.
    Searches emails by sender or keyword.
    Saves emails as .txt and .html files.
    Supports deletion of emails based on sender.
    Uses SOCKS5 proxy (Tor) for secure connections.
    Verbose mode for detailed logging.

Installation

Ensure you have Python 3 installed and install the required dependencies:

pip install colorama pysocks

Configuration
1. Email Accounts Configuration (imap.parse.config.ini)

This file should contain email credentials in the format:

email@example.com:password123
another.email@example.com:password456

2. IMAP Server Configuration (imap.config.ini)

This file should define the IMAP servers for different email providers in the format:

example.com:imap.example.com:993
another.com:imap.another.com:993

Each line contains:
[email domain]:[IMAP server address]:[IMAP port]
Usage

Run the script with one of the following options:

python imap_parser.py -s sender@example.com

This searches for emails from sender@example.com and saves them.

python imap_parser.py -k "important keyword"

This searches for emails containing "important keyword" in their content.

python imap_parser.py -sd spammer@example.com

This searches for emails from spammer@example.com and deletes them.
Additional Options

    -p → Use SOCKS5 proxy (Tor)
    -v → Enable verbose output

Example with proxy and verbose mode:

python imap_parser.py -s sender@example.com -p -v

Output

Emails are saved in the ./results directory:

results/
  ├── sender@example.com/
  │   ├── 20240313_123456_Subject.txt
  │   ├── 20240313_123456_Subject.html
  ├── another@example.com/
  │   ├── 20240312_101112_Subject.txt
  │   ├── 20240312_101112_Subject.html

    TXT files contain the raw email content.
    HTML files (if available) contain the email's HTML body.

Notes

    Ensure the imap.parse.config.ini and imap.config.ini files are correctly set up before running the script.
    Use Tor or a VPN when using the -p flag for anonymity.
    Deleted emails cannot be recovered after execution.

License

This script is released under the MIT License.
Troubleshooting
"IMAP config file not found"

Ensure imap.config.ini exists and contains valid IMAP server details.
"Login failed"

Check if the email credentials in imap.parse.config.ini are correct. Some providers may require app-specific passwords.
"No emails found"

Try adjusting the search criteria (-s, -k) or verify that the inbox contains matching emails.