import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Load environment variables from .env file in project root
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '..', '.env'))

model = SentenceTransformer('all-MiniLM-L6-v2')  # free, fast model

def vectorize_email(subject, body):
    text = f"{subject}. {body[:500]}"  # combine subject + first 500 chars
    vector = model.encode(text).tolist()
    return vector

def get_user_profile():
    raw_keywords = os.getenv("USER_PROFILE_KEYWORDS", "")
    if raw_keywords:
        return [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
    return [
        "college admission deadline",
        "internship offer letter",
        "exam schedule",
        "fee payment last date"
    ]

# For backward compatibility
USER_PROFILE = get_user_profile()

def get_profile_vectors():
    keywords = get_user_profile()
    return [model.encode(kw).tolist() for kw in keywords]