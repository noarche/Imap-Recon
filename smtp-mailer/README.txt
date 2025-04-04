This SMTP Mailer script is a powerful tool for sending bulk emails while handling connection retries, proxies, and tracking sent recipients to avoid duplicates. It is ideal for scenarios like newsletter campaigns or automated messaging while respecting email service limits.

The SMTP Mailer script is a Python tool that sends emails through SMTP servers. It handles retries for SMTP connections, supports proxy usage, and manages sending to multiple recipients while ensuring each email is sent only once per recipient. The script also allows for verbose output, provides a maximum email send limit, and can cache known SMTP servers and sent recipients.
Features:

    Resolves SMTP servers using subdomains.
    Supports using proxy servers (if proxies.txt is available).
    Avoids resending emails to previously sent recipients (tracked via sent_recipients.json).
    Caches known SMTP servers to speed up future connections.
    Configurable maximum number of emails to send per credential.
    Verbose mode for detailed output.
    SMTP connection retries on failure.
    Colors output for improved visibility using colorama.

Prerequisites

Before running the script, ensure you have the following dependencies installed:

pip install colorama pysocks

You should also prepare the following files:

    credentials.txt: Contains the email credentials (in the format email:password).
    who2mail.txt: Contains a list of recipient email addresses to send messages to.
    outgoing.txt: Contains the message body to be sent in each email.
    proxies.txt (optional): Contains a list of proxy servers to rotate through, in the format ip:port.

Configuration Files

    smtp.known.config.json: A JSON file to store cached SMTP server information.
    sent_recipients.json: A JSON file to store the list of recipients to avoid resending emails.

Usage
Command-line Arguments

    -max (optional): Set the maximum number of emails to send per credential. If not specified, the script will send emails to all available recipients.
    -proxy (optional): Use proxies listed in proxies.txt for email sending.
    -v / --verbose (optional): Enable verbose output for more detailed logging.

Basic Example:

python smtp_mailer.py -max 10 -v

This command will:

    Send a maximum of 10 emails per credential.
    Enable verbose output for debugging.

Proxy Support

To use proxies, create a proxies.txt file with proxy server addresses in the format ip:port. When you run the script with the -proxy flag, it will use these proxies in a round-robin fashion.

Example of proxies.txt:

192.168.1.1:1080
192.168.1.2:1080

Files Overview

    credentials.txt:
        Format: email:password (one per line).
        Example:

user@example.com:password123
anotheruser@example.com:anotherpassword

who2mail.txt:

    List of recipient email addresses.
    Example:

recipient1@example.com
recipient2@example.com

outgoing.txt:

    Contains the email body (one per line).
    Example:

Hello, this is a test email.
Best regards,
Your Name

proxies.txt (Optional):

    List of proxy server addresses.
    Example:

    192.168.1.1:1080
    192.168.1.2:1080

Flow

    SMTP Server Resolution:
        The script attempts to resolve the SMTP server using predefined subdomains (smtp, mail, relay, etc.). If the server is already known, it uses the cached value from smtp.known.config.json.

    SMTP Connection:
        The script tries to connect to the SMTP server using ports 587 and 465 (TLS and SSL).
        It retries connecting to the server and tries to send emails with a 5-second timeout.

    Email Sending:
        It sends emails to recipients in who2mail.txt (excluding those already in sent_recipients.json).
        It supports a maximum email count per credential (-max), and it pauses for 1 second between each email to avoid spamming.

    Proxies:
        If proxies are provided, the script uses them in a round-robin fashion to distribute the load.

    Error Handling:
        The script handles failed SMTP connections and email sending errors gracefully. It will print relevant error messages and continue processing the next credential.

    Result Caching:
        Sent recipients are cached in sent_recipients.json to prevent duplicate emails.
        Known SMTP servers are cached in smtp.known.config.json for faster resolution in future runs.

Error Handling

The script has several layers of error handling:

    SMTP Connection Failures: If a connection to the SMTP server fails, the script will try the next available port.
    Invalid Credentials Format: If the credentials in credentials.txt are in the wrong format (email:password), the script will notify you of the error.
    File Not Found: If any required file (credentials.txt, who2mail.txt, outgoing.txt, etc.) is missing, the script will notify you and stop execution.

Example Output

[?] Enter email subject: Test Email
[✓] Connection successful: smtp.gmail.com:587
[+] Sent to recipient1@example.com from user@example.com
[+] Sent to recipient2@example.com from user@example.com
[!] Failed to send to recipient3@example.com: SMTPException


