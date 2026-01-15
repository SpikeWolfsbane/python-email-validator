#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MIT License
# 
# Copyright (c) 2026 Daniel Franklin (@spikewolfsbane)
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import re
import requests
from typing import List, Dict
import os
import dns.resolver
from dns.exception import DNSException
import argparse
import csv
from tqdm import tqdm

DISPOSABLE_DOMAINS: set[str] = set()

def load_disposable_domains():
    global DISPOSABLE_DOMAINS
    file_path = 'disposable_email_blocklist.conf'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                domain = line.strip().lower()
                if domain and not domain.startswith('#'):
                    DISPOSABLE_DOMAINS.add(domain)
        print(f"Loaded {len(DISPOSABLE_DOMAINS)} disposable domains from local list")
    else:
        print("Warning: File not found, fallback to API")

load_disposable_domains()

def is_valid_email_format(email: str) -> bool:
    """Check basic email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_disposable_email(email: str) -> bool:
    """Check if email domain is disposable: local list first (fast/offline), then API fallback."""
    domain = email.split('@')[-1].lower()
    
    if domain in DISPOSABLE_DOMAINS:  
        return True
    
  #   API fallback only if local missed it
  #  try:
  #      response = requests.get(f"https://api.mailchecker.net/v1/check?email={email}", timeout=5)
  #      if response.status_code == 200:
  #          data = response.json()
  #          return data.get('disposable', False)
  #   except Exception as e:
  #      print(f"API disposable check failed for {email}: {e} (local list used only)")
    
    return False

def has_mx_record(domain: str) -> bool:
    """Check if the domain has at least one valid MX record (mail server exists)."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout, DNSException):
        return False

def validate_emails(emails: List[str]) -> List[Dict[str, any]]:
    """Validate a list of emails and return a list of result dictionaries.
    
    Each result includes: email, valid_format, disposable, mx_valid, status.
    """
    results = []
    for email in emails:
        email = email.strip().lower()
        if not email:
            continue
            
        valid_format = is_valid_email_format(email)
        is_disposable = False
        mx_valid = False
        status = 'Invalid format'
        
        if valid_format:
            is_disposable = is_disposable_email(email)
            if is_disposable:
                status = 'Disposable'
            else:
                domain = email.split('@')[-1]
                mx_valid = has_mx_record(domain)
                if mx_valid:
                    status = 'Valid'
                else:
                    status = 'No MX record (domain invalid)'
        
        results.append({
            'email': email,
            'valid_format': valid_format,
            'disposable': is_disposable,
            'mx_valid': mx_valid,          
            'status': status
        })
    
    return results

def read_emails_from_file(input_file: str) -> list[str]:
    """Read one email per line from a text file, strip whitespace, skip empties."""
    emails = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip()
                if email:  # skip empty lines
                    emails.append(email)
        print(f"Read {len(emails)} emails from {input_file}")
        return emails
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def save_results_to_csv(results: list[dict], output_file: str) -> None:
    """Save validation results to CSV with all columns."""
    if not results:
        print("No results to save.")
        return
    
    fieldnames = ['email', 'valid_format', 'disposable', 'mx_valid', 'status']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Results saved to {output_file} ({len(results)} emails processed)")
    except Exception as e:
        print(f"Error saving CSV: {e}")

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bulk Email Validator: Syntax + Disposable + MX Checks",
        epilog="""
Examples:
  python email_validator.py --input emails.txt
  python email_validator.py --input list.txt --output clean.csv
  python email_validator.py --input emails.txt --verbose   # shows per-email details in terminal

Features:
  - Syntax validation (regex)
  - Disposable/temporary domain detection (local list with ~5087 entries)
  - MX record check (verifies domain has mail servers)
  - Progress bar + clean CSV output with all validation details
  - Summary stats (counts & percentages)

Notes:
  - Fully local disposable list + DNS lookups (no external API calls)
  - Fast for small/medium lists; DNS lookups are the main bottleneck for large files
  - Run with --verbose to see per-email details in terminal
  - Requires: dnspython, tqdm (pip install dnspython tqdm)

For questions or updates: check the GitHub repo (coming soon).
""",
        formatter_class=argparse.RawDescriptionHelpFormatter  # preserves line breaks and formatting
    )

    parser.add_argument('--input', type=str, required=True,
                        help="Input text file with one email per line")
    parser.add_argument('--output', type=str, default='validated_emails.csv',
                        help="Output CSV file (default: validated_emails.csv)")
    parser.add_argument('--verbose', action='store_true',
                        help="Print detailed per-email results to terminal (in addition to CSV)")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()
    
    # Read emails from file
    emails = read_emails_from_file(args.input)
    if not emails:
        print("No emails to process. Exiting.")
        exit(1)
    
    # Validate with progress bar
    print("Starting validation...")
    results = []
    for email in tqdm(emails, desc="Validating emails", unit="email"):
        # We validate one at a time (you can later add batching if needed)
        single_result_list = validate_emails([email])  # pass list of 1
        results.extend(single_result_list)
    
    # Save to CSV
    save_results_to_csv(results, args.output)
    
    if args.verbose:
        print("\nDetailed Results:")
        print("-" * 60)
        for r in results:
            print(f"Email: {r['email']}")
            print(f"  Valid format   : {r['valid_format']}")
            print(f"  Disposable     : {r['disposable']}")
            print(f"  MX valid       : {r['mx_valid']}")
            print(f"  Status         : {r['status']}")
            print("-" * 60)

    # Optional: still print summary to terminal
    print("\n" + "=" * 50)
    print("Validation Summary")
    print("=" * 50)
    print(f"Total emails processed: {len(results):,}")
    
    status_counts = {}
    for r in results:
        status = r['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100 if results else 0
        print(f"{status:<30} {count:>6} ({percentage:5.1f}%)")
    
    print("=" * 50)