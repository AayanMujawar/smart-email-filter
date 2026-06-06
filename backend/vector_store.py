import pinecone
from vectorizer import vectorize_email

pc = pinecone.Pinecone(api_key="YOUR_KEY")
index = pc.Index("emails")

def save_email(email_id, subject, body, metadata):
    vector = vectorize_email(subject, body)
    index.upsert([(email_id, vector, metadata)])