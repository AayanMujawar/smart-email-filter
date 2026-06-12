import dateparser
import re
from datetime import datetime

DEADLINE_KEYWORDS = [
    'deadline', 'last date', 'due', 'submit', 'before', 'expires', 
    'closing', 'apply', 'by', 'need', 'must', 'reply', 'respond', 
    'action required'
]

# Regexes for various date formats to find candidates in text
DATE_PATTERNS = [
    # Month Day, Year (e.g., June 30, 2026 or June 30th 2026)
    r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*|\s+)\d{4}\b',
    # Day Month Year (e.g., 15th July 2026 or 15 July 2026)
    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s*,\s*|\s+)\d{4}\b',
    # Month Day (e.g., June 30 or June 30th)
    r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\b',
    # Day Month (e.g., 15th July or 15 July)
    r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b',
    # Numeric dates: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, etc.
    r'\b\d{1,4}[-./]\d{1,2}[-./]\d{2,4}\b',
    # Relative terms
    r'\b(?:tomorrow|today)\b'
]

COMBINED_PATTERN = '|'.join(f'({p})' for p in DATE_PATTERNS)

def extract_deadline(text):
    if not text:
        return None
    
    text_lower = text.lower()
    matches = []
    
    # Extract all candidate dates matching our regex patterns
    for match in re.finditer(COMBINED_PATTERN, text_lower):
        matches.append((match.group(), match.start(), match.end()))
        
    if not matches:
        return None
        
    # Check each candidate date for deadline-related keywords in its vicinity
    for match_str, start, end in matches:
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 20)
        context_text = text_lower[context_start:context_end]
        
        if any(kw in context_text for kw in DEADLINE_KEYWORDS):
            parsed_date = dateparser.parse(match_str)
            if parsed_date:
                return parsed_date
                        
    return None
