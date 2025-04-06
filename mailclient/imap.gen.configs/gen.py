#!/usr/bin/env python3

import os
import configparser
import argparse
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate individual INI files from accounts.txt and services.ini.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    return parser.parse_args()

def load_services_config(filename="services.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    sections = config.sections()

    if not sections:
        print(Fore.RED + "[ERROR] No services found in services.ini.")
        exit(1)

    if len(sections) > 1:
        print(Fore.CYAN + "[INFO] Multiple services found. Please select one:")
        for idx, section in enumerate(sections, 1):
            print(f"{idx}. {section}")
        try:
            choice = int(input(Fore.YELLOW + "Enter the number of the service to use: "))
            if choice < 1 or choice > len(sections):
                raise ValueError
            selected_section = sections[choice - 1]
        except ValueError:
            print(Fore.RED + "[ERROR] Invalid selection.")
            exit(1)
    else:
        selected_section = sections[0]

    try:
        imap_host = config.get(selected_section, "imap_host")
        smtp_host = config.get(selected_section, "smtp_host")
        return imap_host, smtp_host
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(Fore.RED + f"[ERROR] Failed to read services.ini: {e}")
        exit(1)

def read_accounts(filename="accounts.txt"):
    if not os.path.exists(filename):
        print(Fore.RED + f"[ERROR] {filename} not found.")
        exit(1)

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

    # Ensure the configs directory exists
    os.makedirs("configs", exist_ok=True)
    filename = os.path.join("configs", f"{email}.ini")
    with open(filename, "w") as configfile:
        config.write(configfile)

    if verbose:
        print(Fore.GREEN + f"[INFO] Created {filename}")

def main():
    args = parse_args()
    imap_host, smtp_host = load_services_config()
    accounts = read_accounts()

    if args.verbose:
        print(Fore.CYAN + f"[INFO] Found {len(accounts)} account(s) to process.")

    for idx, line in enumerate(accounts, 1):
        try:
            email, password = line.split(":", 1)
            create_ini_file(email, password, imap_host, smtp_host, idx, args.verbose)
        except ValueError:
            print(Fore.YELLOW + f"[WARN] Skipping malformed line: {line}")

    if not args.verbose:
        print(Fore.GREEN + "[DONE] Configuration files generated.")

if __name__ == "__main__":
    main()
