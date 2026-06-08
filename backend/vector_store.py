import os
from dotenv import load_dotenv
from pinecone import Pinecone
from vectorizer import vectorize_email

# Load environment variables from .env file in project root
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, '..', '.env'))

api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME", "emails")

if not api_key:
    raise ValueError("PINECONE_API_KEY is not set in environment or .env file.")

pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)

def save_email(email_id, subject, body, metadata):
    vector = vectorize_email(subject, body)
    index.upsert(vectors=[{"id": email_id, "values": vector, "metadata": metadata}])
