import imaplib
import email
import os
import argparse
import socks
import socket
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def load_accounts(file):
    accounts = []
    try:
        with open(file, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) == 2:
                    accounts.append((parts[0], parts[1]))
    except FileNotFoundError:
        print(Fore.RED + f"[-] Config file {file} not found.")
    return accounts

def get_imap_server(domain, imap_config):
    try:
        with open(imap_config, 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) == 3 and parts[0] == domain:
                    return parts[1], parts[2]
    except FileNotFoundError:
        print(Fore.RED + f"[-] IMAP config file {imap_config} not found.")
    return None, None

def connect_imap(email_address, password, imap_server, imap_port, use_proxy):
    if use_proxy:
        socks.setdefaultproxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
    
    try:
        mail = imaplib.IMAP4_SSL(imap_server, int(imap_port))
        mail.login(email_address, password)
        print(Fore.GREEN + f"[+] Connected to {email_address}.")
        return mail
    except Exception as e:
        print(Fore.RED + f"[-] IMAP connection error for {email_address}: {e}")
        return None

def search_mail(mail, search_criterion, verbose):
    try:
        mail.select('inbox')
        result, data = mail.search(None, search_criterion)
        if result != 'OK':
            print(Fore.RED + "[-] No emails found.")
            return []
        email_ids = data[0].split()
        if verbose:
            print(Fore.CYAN + f"[+] Found {len(email_ids)} emails.")
        return email_ids
    except Exception as e:
        print(Fore.RED + f"[-] Error searching emails: {e}")
        return []

def delete_emails(mail, email_ids):
    try:
        for email_id in email_ids:
            mail.store(email_id, '+FLAGS', '\\Deleted')
        mail.expunge()
        print(Fore.GREEN + f"[+] Deleted {len(email_ids)} emails.")
    except Exception as e:
        print(Fore.RED + f"[-] Error deleting emails: {e}")

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

def decode_subject(subject):
    decoded_parts = []
    for part, encoding in email.header.decode_header(subject or 'No_Subject'):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return sanitize_filename('_'.join(decoded_parts).replace(' ', '_')[:50])

def extract_email_date(msg):
    date_header = msg['Date']
    if date_header:
        try:
            return parsedate_to_datetime(date_header).strftime('%Y%m%d_%H%M%S')
        except Exception:
            pass
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def save_email(mail, email_id, save_path, save_as_text=False):
    try:
        result, data = mail.fetch(email_id, '(RFC822)')
        if result != 'OK':
            print(Fore.RED + f"[-] Failed to fetch email ID {email_id}.")
            return
        
        msg = email.message_from_bytes(data[0][1])
        subject = decode_subject(msg['Subject'])
        email_date = extract_email_date(msg)
        os.makedirs(save_path, exist_ok=True)
        
        # Save email as HTML
        html_file = f"{save_path}/{email_date}_{subject}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    f.write(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
                    break
            else:
                # If no HTML part, save the plain text part
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        f.write(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
                        break
        
        print(Fore.GREEN + f"[+] Email saved as HTML: {html_file}")

        # Save email as text if requested
        if save_as_text:
            text_file = f"{save_path}/{email_date}_{subject}.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(msg.as_string())
            print(Fore.GREEN + f"[+] Email saved as text: {text_file}")

    except Exception as e:
        print(Fore.RED + f"[-] Error saving email ID {email_id}: {e}")

def save_email_with_attachments(mail, email_id, save_path, save_as_text=False):
    """Save email with attachments."""
    try:
        result, data = mail.fetch(email_id, '(RFC822)')
        if result != 'OK':
            print(Fore.RED + f"[-] Failed to fetch email ID {email_id}.")
            return

        msg = email.message_from_bytes(data[0][1])
        subject = decode_subject(msg['Subject'])
        email_date = extract_email_date(msg)
        os.makedirs(save_path, exist_ok=True)

        # Save email as HTML
        html_file = f"{save_path}/{email_date}_{subject}.html"
        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        f.write(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
                        break
                else:
                    # If no HTML part, save the plain text part
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            f.write(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
                            break
            print(Fore.GREEN + f"[+] Email saved as HTML: {html_file}")
        except Exception as e:
            print(Fore.RED + f"[-] Error saving email as HTML: {e}")

        # Save email as text if requested
        if save_as_text:
            try:
                text_file = f"{save_path}/{email_date}_{subject}.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(msg.as_string())
                print(Fore.GREEN + f"[+] Email saved as text: {text_file}")
            except Exception as e:
                print(Fore.RED + f"[-] Error saving email as text: {e}")

        # Save attachments
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    try:
                        sanitized_filename = sanitize_filename(filename)
                        attachment_path = os.path.join(save_path, sanitized_filename)
                        with open(attachment_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        print(Fore.GREEN + f"[+] Attachment saved: {attachment_path}")
                    except Exception as e:
                        print(Fore.RED + f"[-] Error saving attachment {filename}: {e}")

    except Exception as e:
        print(Fore.RED + f"[-] Error saving email ID {email_id} with attachments: {e}")

def process_sent_folder(mail, save_path, save_as_text=False):
    """Process the Sent folder and save emails with attachments."""
    try:
        mail.select('"[Gmail]/Sent Mail"' if 'gmail' in mail.host else 'Sent')
        result, data = mail.search(None, 'ALL')
        if result != 'OK':
            print(Fore.RED + "[-] No emails found in Sent folder.")
            return

        email_ids = data[0].split()
        print(Fore.CYAN + f"[+] Found {len(email_ids)} emails in Sent folder.")

        for email_id in email_ids:
            save_email_with_attachments(mail, email_id, save_path, save_as_text)
    except Exception as e:
        print(Fore.RED + f"[-] Error processing Sent folder: {e}")

def main():
    parser = argparse.ArgumentParser(description='IMAP Email Parser')
    parser.add_argument('-v', action='store_true', help='Verbose output')
    parser.add_argument('-p', action='store_true', help='Use SOCKS5 proxy')
    parser.add_argument('-s', type=str, help='Search by sender')
    parser.add_argument('-k', type=str, help='Search by keyword')
    parser.add_argument('-sd', type=str, help='Search by sender and delete emails')
    parser.add_argument('-sa', action='store_true', help='Download all emails with attachments from Sent folder')
    parser.add_argument('-txt', action='store_true', help='Save emails as both HTML and text')
    args = parser.parse_args()
    
    accounts = load_accounts('imap.parse.config.ini')
    if not accounts:
        print(Fore.RED + "[-] No accounts found.")
        return
    
    search_criterion = None
    save_dir = "./results"
    delete_emails_flag = False
    
    if args.s:
        search_criterion = f'FROM "{args.s}"'
        save_dir += f"/{args.s}"
    elif args.k:
        search_criterion = f'TEXT "{args.k}"'
        save_dir += f"/{args.k}"
    elif args.sd:
        search_criterion = f'FROM "{args.sd}"'
        delete_emails_flag = True
    elif args.sa:
        save_dir += "/sent"
    else:
        print(Fore.RED + "[-] Must specify -s, -k, -sd, or -sa.")
        return
    
    for email_address, password in accounts:
        domain = email_address.split('@')[-1]
        imap_server, imap_port = get_imap_server(domain, 'imap.config.ini')
        if not imap_server:
            print(Fore.RED + f"[-] IMAP server not found for {email_address}.")
            continue
        
        mail = connect_imap(email_address, password, imap_server, imap_port, args.p)
        if not mail:
            continue
        
        try:
            if args.sa:
                process_sent_folder(mail, f"{save_dir}/{email_address}", args.txt)
            else:
                email_ids = search_mail(mail, search_criterion, args.v)
                if delete_emails_flag:
                    delete_emails(mail, email_ids)
                else:
                    for email_id in email_ids:
                        try:
                            save_email(mail, email_id, f"{save_dir}/{email_address}")
                        except Exception as e:
                            print(Fore.RED + f"[-] Error processing email ID {email_id}: {e}")
        except Exception as e:
            print(Fore.RED + f"[-] Error processing account {email_address}: {e}")
        finally:
            try:
                mail.logout()
                print(Fore.GREEN + f"[+] Logged out from {email_address}.")
            except Exception as e:
                print(Fore.RED + f"[-] Error logging out from {email_address}: {e}")

    print(Fore.GREEN + "[+] Done.")

if __name__ == "__main__":
    main()
