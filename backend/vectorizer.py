from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # free, fast model

def vectorize_email(subject, body):
    text = f"{subject}. {body[:500]}"  # combine subject + first 500 chars
    vector = model.encode(text).tolist()
    return vector