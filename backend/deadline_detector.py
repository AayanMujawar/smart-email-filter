import dateparser
import re
from datetime import datetime

DEADLINE_KEYWORDS = [
    'deadline', 'last date', 'due date', 'submit by',
    'expires', 'closing date', 'apply before'
]

def extract_deadline(text):
    text_lower = text.lower()
    for kw in DEADLINE_KEYWORDS:
        if kw in text_lower:
            # Find the date near the keyword
            idx = text_lower.find(kw)
            snippet = text[max(0,idx-20):idx+80]
            parsed = dateparser.parse(snippet)
            if parsed:
                return parsed
    return None