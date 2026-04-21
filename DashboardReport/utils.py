import re
import html

def sanitize_content(text):
    if not isinstance(text, str): return text
    
    # Mask amsin domains and subdomains
    text = re.sub(r'https?://[a-zA-Z0-9.-]*amsin\.hirepro\.in[^\s"\'<>]*', 'https://[MASKED_INTERNAL_URL]', text, flags=re.IGNORECASE)
    
    # Mask hirepro internal links that might look like /test-all-hirepro-files/
    text = re.sub(r'/(?:test-all-hirepro-files|zwayam|hirepro-reports)/[a-zA-Z0-9._/-]*', '/[MASKED_PATH]/', text, flags=re.IGNORECASE)
    
    # Mask AWS Access Keys
    text = re.sub(r'AKIA[A-Z0-9]{16}', 'AKIA[MASKED_AWS_KEY]', text)
    
    # Mask potential tokens in URLs (Base64 patterns)
    text = re.sub(r'/(?:home|token|interview)/[a-zA-Z0-9+/=]{30,}', '/[MASKED_TOKEN]/', text)
    
    # Mask S3 signed URL components (Signature, Expires, AWSAccessKeyId, etc.)
    text = re.sub(r'(Signature|Expires|AWSAccessKeyId|X-Amz-Signature|X-Amz-Algorithm|X-Amz-Credential|X-Amz-Date|X-Amz-SignedHeaders|X-Amz-Expires)=[^&\s"\'<>]+', r'\1=[MASKED]', text, flags=re.IGNORECASE)
    
    # Mask internal emails
    text = re.sub(r'[a-zA-Z0-9._%+-]+@hirepro\.in', '[USER]@hirepro.in', text, flags=re.IGNORECASE)
    
    # Mask other emails (PII)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@(?!hirepro\.in)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[MASKED_EMAIL]', text, flags=re.IGNORECASE)
    
    # Mask Indian phone numbers
    text = re.sub(r'\b(?:(?:\+91|0)?[6-9]\d{9})\b', '[MASKED_PHONE]', text)
    
    # Mask PanNo and AadhaarNo patterns
    text = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', '[MASKED_PAN]', text)
    text = re.sub(r'\b\d{12}\b', '[MASKED_AADHAAR]', text)
    
    # Specific amsin without full URL if in a table cell or similar
    text = re.sub(r'\bamsin\b', '[MASKED_REF]', text, flags=re.IGNORECASE)
    
    return text
