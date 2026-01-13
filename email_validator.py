import re
import requests
from typing import List, Dict

def is_valid_email_format(email: str) -> bool:
    """Check basic email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_disposable_email(email: str) -> bool:
    """Check if email domain is from a known disposable provider."""
    domain = email.split('@')[-1].lower()
    
    
    disposable_domains = {
        'mailinator.com', 'tempmail.com', '10minutemail.com', 'guerrillamail.com',
        'yopmail.com', 'throwawaymail.com', 'sharklasers.com', 'dispostable.com'
    }
    
    if domain in disposable_domains:
        return True
    
    try:
         response = requests.get(f"https://api.mailchecker.net/v1/check?email={email}")
         if response.status_code == 200:
             data = response.json()
             return data.get('disposable', False)
    except:
        pass  # fallback to local list if API fails
    
    return False

def validate_emails(emails: List[str]) -> List[Dict]:
    """Validate a list of emails and return results."""
    results = []
    for email in emails:
        email = email.strip().lower()
        if not email:
            continue
            
        valid_format = is_valid_email_format(email)
        is_disposable = is_disposable_email(email) if valid_format else False
        
        results.append({
            'email': email,
            'valid_format': valid_format,
            'disposable': is_disposable,
            'status': 'Valid' if valid_format and not is_disposable else 'Invalid format' if not valid_format else 'Disposable'
        })
    
    return results

# Example usage
if __name__ == "__main__":
    test_emails = [
        "daniel@example.com",
        "test@10minutemail.com",
        "invalid-email",
        "hello@fake.com",
        "spike@dispostable.com",
        ""
    ]
    
    print("Email Validation Results:")
    print("-" * 50)
    results = validate_emails(test_emails)
    
    for r in results:
        print(f"Email: {r['email']}")
        print(f"  Valid format: {r['valid_format']}")
        print(f"  Disposable:   {r['disposable']}")
        print(f"  Status:       {r['status']}")
        print()
