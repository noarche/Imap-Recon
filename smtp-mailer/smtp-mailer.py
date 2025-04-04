import smtplib
import socks
import socket
import time
import argparse
import sys
import json
from email.mime.text import MIMEText
from colorama import Fore, Style, init
from datetime import datetime
import os

# Initialize colorama
init(autoreset=True)

CONFIG_FILE = "smtp.known.config.json"
SENT_CACHE_FILE = "sent_recipients.json"
KNOWN_SMTP = {}
SENT_RECIPIENTS = set()

# Load cached SMTP servers if available
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            KNOWN_SMTP = json.load(f)
    except json.JSONDecodeError:
        KNOWN_SMTP = {}

# Load sent recipients cache
if os.path.exists(SENT_CACHE_FILE):
    try:
        with open(SENT_CACHE_FILE, "r", encoding="utf-8") as f:
            SENT_RECIPIENTS = set(json.load(f))
    except json.JSONDecodeError:
        SENT_RECIPIENTS = set()

SUBDOMAINS = [
    "smtp", "autodiscover", "relay", "imaps", "mail1", "login", "mobile", "mailer",
    "id", "mailbox", "mail2", "secure", "my", "account", "outlook", "inbound",
    "incoming", "mail", "pop", "pop3", "webmail", "imap", "outbound", "wm"
]

def save_sent_recipients():
    with open(SENT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(SENT_RECIPIENTS), f, indent=4)

def load_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File not found: {filename}")
        sys.exit(1)

def resolve_smtp_server(domain):
    if domain in KNOWN_SMTP:
        smtp_entry = KNOWN_SMTP[domain]
        if ":" in smtp_entry:
            smtp_server, port = smtp_entry.split(":")
            return smtp_server, int(port)
        return smtp_entry, None  # Default to no specific port
    
    for subdomain in SUBDOMAINS:
        smtp_server = f"{subdomain}.{domain}"
        try:
            socket.gethostbyname(smtp_server)
            return smtp_server, None  # Default to no specific port
        except socket.gaierror:
            continue
    return None, None

def save_smtp_server(domain, smtp_server):
    KNOWN_SMTP[domain] = smtp_server
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(KNOWN_SMTP, f, indent=4)

def test_smtp_connection(smtp_server, port, debug=False):
    try:
        with socket.create_connection((smtp_server, port), timeout=5):
            if debug:
                print(f"{Fore.GREEN}[✓] Connection successful: {smtp_server}:{port}")
            return True
    except Exception as e:
        if debug:
            print(f"{Fore.YELLOW}[!] Connection failed: {smtp_server}:{port} - {e}")
        return False

def connect_smtp(smtp_server, email, password, proxy=None, debug=False, port=None):
    timeout = 5
    server = None

    if proxy:
        proxy_ip, proxy_port = proxy.split(":")
        socks.setdefaultproxy(socks.SOCKS5, proxy_ip, int(proxy_port))
        socket.socket = socks.socksocket

    ports_to_try = [port] if port else [465, 587]  # Use the specified port if provided
    for port in ports_to_try:
        if not test_smtp_connection(smtp_server, port, debug):
            continue

        try:
            if port == 587:
                server = smtplib.SMTP(smtp_server, port, timeout=timeout)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_server, port, timeout=timeout)

            if debug:
                server.set_debuglevel(1)

            server.login(email, password)
            return server
        except Exception as e:
            print(f"{Fore.YELLOW}[!] Failed on port {port}: {e}")

    return None

def save_working_credential(credential):
    """Save a working credential to a file in real-time."""
    with open("working_credentials.txt", "a", encoding="utf-8") as f:
        f.write(credential + "\n")

def send_email(smtp_server, email, password, recipients, subject, message, max_emails, proxy=None, verbose=False, debug=False):
    try:
        domain = email.split("@")[1]
        smtp_server, port = resolve_smtp_server(domain)
        if not smtp_server:
            print(f"{Fore.RED}[!] No SMTP server found for {domain}")
            return 0, email, [], subject

        server = connect_smtp(smtp_server, email, password, proxy, debug, port)
        if not server:
            print(f"{Fore.RED}[!] Could not connect to SMTP server: {smtp_server}")
            return 0, email, [], subject

        save_smtp_server(domain, f"{smtp_server}:{port}" if port else smtp_server)

        msg = MIMEText(message)
        msg['From'] = email
        msg['Subject'] = subject

        sent_count = 0
        max_limit = max_emails if max_emails else len(recipients)
        
        for recipient in recipients[:max_limit]:
            if recipient in SENT_RECIPIENTS:
                continue
            
            msg['To'] = recipient
            try:
                server.sendmail(email, recipient, msg.as_string())
                sent_count += 1
                SENT_RECIPIENTS.add(recipient)
                print(f"{Fore.GREEN}[+] Sent to {recipient} from {email}")
                
                # Save the working credential only after a successful email
                save_working_credential(f"{email}:{password}")
                
                time.sleep(1)
            except smtplib.SMTPException as e:
                print(f"{Fore.RED}[!] Failed to send to {recipient}: {e}")
                break

        server.quit()
        save_sent_recipients()
        return sent_count, email, recipients[:sent_count], subject

    except Exception as e:
        if verbose:
            print(f"{Fore.RED}[!] Error with {email}: {e}")
        return 0, email, [], subject

def main():
    parser = argparse.ArgumentParser(description="SMTP Mailer - Sends emails while handling SMTP connection retries.")
    parser.add_argument("-max", type=int, default=None, help="Maximum number of emails to send per credential (default: unlimited)")
    parser.add_argument("-proxy", action="store_true", help="Use proxies from proxies.txt")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    credentials = load_list("credentials.txt")
    recipients = [r for r in load_list("who2mail.txt") if r not in SENT_RECIPIENTS]
    message = "\n".join(load_list("outgoing.txt"))

    # Read the subject from the first line of subject.txt
    try:
        with open("subject.txt", "r", encoding="utf-8") as subject_file:
            subject = subject_file.readline().strip()
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File not found: subject.txt")
        sys.exit(1)

    proxies = load_list("proxies.txt") if args.proxy else []
    proxy_index = 0

    if not recipients:
        print(f"{Fore.YELLOW}[!] No new recipients to email.")
        return

    for cred in credentials:
        try:
            email, password = cred.split(":")
            domain = email.split("@")[1]
            smtp_server = resolve_smtp_server(domain)
            if not smtp_server:
                print(f"{Fore.RED}[!] No SMTP server found for {domain}")
                continue
            proxy = proxies[proxy_index] if proxies else None
            send_email(smtp_server, email, password, recipients, subject, message, args.max, proxy, args.verbose)
            if proxies:
                proxy_index = (proxy_index + 1) % len(proxies)
        except ValueError:
            print(f"{Fore.RED}[!] Invalid credentials format in credentials.txt: {cred}")

if __name__ == "__main__":
    main()
