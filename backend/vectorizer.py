from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # free, fast model

def vectorize_email(subject, body):
    text = f"{subject}. {body[:500]}"  # combine subject + first 500 chars
    vector = model.encode(text).tolist()
    return vector
# User's custom profile
USER_PROFILE = [
    "college admission deadline",
    "internship offer letter",
    "exam schedule",
    "fee payment last date"
]

def get_profile_vectors():
    return [model.encode(kw).tolist() for kw in USER_PROFILE]