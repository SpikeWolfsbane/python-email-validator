# Python Email Validator

A bulk email checker tool written in Python. Validates email lists for syntax, disposable/temporary domains, and MX record existence. Outputs a clean CSV report with progress bar and summary stats.

## Features
- **Syntax validation**: Uses regex to check basic email format.
- **Disposable detection**: Offline check against a local list of ~5087 known disposable domains (from [disposable-email-domains repo](https://github.com/disposable-email-domains/disposable-email-domains)).
- **MX record check**: Verifies if the domain has mail servers via DNS lookup.
- **Bulk processing**: Input from TXT file (one email per line), output to CSV with all details.
- **Progress bar**: Powered by tqdm for long runs.
- **Summary stats**: Counts and percentages of valid/disposable/invalid.
- **Verbose mode**: Optional detailed per-email output in terminal.

## Installation
1. Clone the repo or download the files.
2. Install dependencies:
   ```bash
   pip install dnspython tqdm