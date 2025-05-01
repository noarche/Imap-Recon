#!/usr/bin/env python3
import os
import json
import argparse
import glob
import random
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

CHECKED_DIR = './checked/'
CHECKED_JSON = os.path.join(CHECKED_DIR, 'checked.json')
OUTPUT_DIR = './wordlist/'


def verbose_print(verbose, msg):
    if verbose:
        print(f"{Fore.YELLOW}[VERBOSE]{Style.RESET_ALL} {msg}")


def count_checked_entries():
    if os.path.exists(CHECKED_JSON):
        with open(CHECKED_JSON, 'r', encoding='utf-8') as f:
            return len(json.load(f))
    return 0


class CustomHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        super().add_usage(usage, actions, groups, prefix)
        count = count_checked_entries()
        self._add_item(lambda: f"\n{Fore.MAGENTA}[*] {count} entries currently in checked.json{Style.RESET_ALL}\n", [])


def valid_email_line(line):
    return line.count('@') == 1


def load_checked():
    if os.path.exists(CHECKED_JSON):
        with open(CHECKED_JSON, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_checked(entries, verbose=False):
    sorted_entries = sorted(entries)
    with open(CHECKED_JSON, 'w', encoding='utf-8') as f:
        json.dump(sorted_entries, f, indent=2)
    verbose_print(verbose, f"Updated checked.json with {len(sorted_entries)} total unique entries")


def collect_checked(verbose=False):
    os.makedirs(CHECKED_DIR, exist_ok=True)
    existing_checked = load_checked()

    for filepath in glob.glob(os.path.join(CHECKED_DIR, '*.txt')):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = {line.strip() for line in f if valid_email_line(line.strip())}
            verbose_print(verbose, f"Read {len(lines)} valid lines from {filepath}")
            existing_checked.update(lines)
        os.remove(filepath)
        verbose_print(verbose, f"Deleted {filepath}")

    save_checked(existing_checked, verbose)
    print(f"{Fore.GREEN}[✓]{Style.RESET_ALL} Consolidated .txt files into {CHECKED_JSON}")


def filter_wordlist(input_file, verbose=False):
    if not os.path.exists(input_file):
        print(f"{Fore.RED}[!]{Style.RESET_ALL} Input file does not exist: {input_file}")
        return

    checked = load_checked()

    with open(input_file, 'r', encoding='utf-8') as f:
        input_lines = [line.strip() for line in f if valid_email_line(line.strip())]
    verbose_print(verbose, f"Loaded {len(input_lines)} valid lines from {input_file}")

    new_lines = list(set(input_lines) - checked)
    checked.update(input_lines)  # Always update with all valid lines

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    random.shuffle(new_lines)

    output_file = os.path.join(OUTPUT_DIR, f"wordlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in new_lines:
            f.write(line + '\n')
    print(f"{Fore.CYAN}[✓]{Style.RESET_ALL} Saved {len(new_lines)} new entries to {output_file}")

    save_checked(checked, verbose)


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate checked wordlists and filter new ones.",
        formatter_class=CustomHelpFormatter
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Path to input text file to filter", required=False
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()
    collect_checked(verbose=args.verbose)

    if args.input:
        filter_wordlist(args.input, verbose=args.verbose)
    else:
        print(f"{Fore.BLUE}[*]{Style.RESET_ALL} No input file provided. Only checked.json was updated.")


if __name__ == "__main__":
    main()
