#!/usr/bin/env python3

import os
import configparser
import argparse
from colorama import init, Fore

# Initialize colorama
init(autoreset=True)

ACCOUNTS_DIR = './accounts'
CONFIGS_DIR = './configs'
IMAP_DOMAINS_FILE = './imapdomains.dat'

def parse_args():
    parser = argparse.ArgumentParser(description="Generate INI files from account list and service configuration.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    return parser.parse_args()

def list_account_files():
    if not os.path.exists(ACCOUNTS_DIR):
        os.makedirs(ACCOUNTS_DIR)
    files = [f for f in os.listdir(ACCOUNTS_DIR) if f.endswith(".txt")]
    if not files:
        print(Fore.RED + "[ERROR] No .txt account files found in './accounts'.")
        exit(1)
    return files

def find_in_imapdomains(domain):
    if not os.path.exists(IMAP_DOMAINS_FILE):
        print(Fore.RED + f"[ERROR] {IMAP_DOMAINS_FILE} not found.")
        return None, None

    with open(IMAP_DOMAINS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":")
            if len(parts) == 3 and parts[0].lower() == domain.lower():
                imap_host = f"{parts[1]}:{parts[2]}"
                smtp_host = f"{parts[1]}:587"
                return imap_host, smtp_host

    print(Fore.RED + f"[ERROR] Domain '{domain}' not found in {IMAP_DOMAINS_FILE}.")
    return None, None

def read_accounts(filename):
    if not os.path.exists(filename):
        print(Fore.RED + f"[ERROR] {filename} not found.")
        return []

    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip() and ":" in line]
    return lines

def create_ini_file(email, password, imap_host, smtp_host, index, verbose=False):
    config = configparser.ConfigParser()
    section_name = f"Account{index}"
    config[section_name] = {
        "email": email,
        "imap_host": imap_host,
        "smtp_host": smtp_host,
        "username": email,
        "password": password
    }

    os.makedirs(CONFIGS_DIR, exist_ok=True)
    filename = os.path.join(CONFIGS_DIR, f"{email}.ini")
    if os.path.exists(filename):
        if verbose:
            print(Fore.YELLOW + f"[INFO] Skipping {filename} (already exists).")
        return

    with open(filename, "w") as configfile:
        config.write(configfile)

    if verbose:
        print(Fore.GREEN + f"[INFO] Created {filename}")

def process_account_file(filename, verbose=False):
    accounts = read_accounts(filename)

    if verbose:
        print(Fore.CYAN + f"[INFO] Found {len(accounts)} account(s) in {os.path.basename(filename)}")

    for idx, line in enumerate(accounts, 1):
        try:
            email, password = line.split(":", 1)
            domain = email.split("@")[-1]
            imap_host, smtp_host = find_in_imapdomains(domain)
            if not imap_host or not smtp_host:
                print(Fore.YELLOW + f"[WARN] Skipping account {email} due to missing service configuration.")
                continue
            create_ini_file(email, password, imap_host, smtp_host, idx, verbose)
        except ValueError:
            print(Fore.YELLOW + f"[WARN] Skipping malformed line: {line}")

    if not verbose:
        print(Fore.GREEN + "[DONE] Configuration files generated.")

def main():
    args = parse_args()

    files = list_account_files()
    for file in files:
        filepath = os.path.join(ACCOUNTS_DIR, file)
        if args.verbose:
            print(Fore.CYAN + f"[INFO] Processing file: {file}")
        process_account_file(filepath, args.verbose)

    print(Fore.GREEN + "[DONE] All account files processed.")

if __name__ == "__main__":
    main()
