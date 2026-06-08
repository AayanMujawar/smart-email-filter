import os
import sys

# Ensure backend directory is in the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
sys.path.append(backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, '..', '.env'))

print("="*60)
print("             SMART EMAIL FILTER PIPELINE TEST")
print("="*60)

# Step 1: Test Vectorizer
print("\n[Step 1/4] Testing Email Vectorizer...")
try:
    import vectorizer
    print("SUCCESS: Vectorizer module imported successfully.")
    sample_subject = "Urgent: College Admission Deadline Extended!"
    sample_body = "Dear student, the deadline for submitting your college admission form has been extended to June 15th. Please pay your fees before the last date."
    print(f"  Subject: '{sample_subject}'")
    print(f"  Body: '{sample_body[:60]}...'")
    
    vector = vectorizer.vectorize_email(sample_subject, sample_body)
    print(f"SUCCESS: Vectorization successful! Vector dimension: {len(vector)}")
    print(f"  First 5 dimensions: {vector[:5]}")
except Exception as e:
    print(f"ERROR: Error in Vectorizer: {e}")
    vector = None

# Step 2: Test Keyword Profile System
print("\n[Step 2/4] Testing Keyword Profile System...")
try:
    print(f"  User Keywords Profile: {vectorizer.USER_PROFILE}")
    profile_vectors = vectorizer.get_profile_vectors()
    print(f"SUCCESS: Successfully vectorized user profile. Vector count: {len(profile_vectors)}")
except Exception as e:
    print(f"ERROR: Error in Keyword Profile System: {e}")
    profile_vectors = None

# Step 3: Test Scoring Engine
print("\n[Step 3/4] Testing Scoring Engine (Cosine Similarity)...")
if vector is not None and profile_vectors is not None:
    try:
        import scorer
        score = scorer.score_email(vector, profile_vectors)
        print("SUCCESS: Scorer module imported successfully.")
        print(f"SUCCESS: Calculated match score: {score:.4f} (0.0 to 1.0 scale)")
        
        # Test with a low-priority email
        junk_subject = "Win a free cruise now!"
        junk_body = "Click this link to claim your reward of one million dollars instantly."
        junk_vector = vectorizer.vectorize_email(junk_subject, junk_body)
        junk_score = scorer.score_email(junk_vector, profile_vectors)
        print(f"SUCCESS: Junk email score: {junk_score:.4f}")
        print(f"  Comparison: Urgent Email Score ({score:.4f}) vs Junk Email Score ({junk_score:.4f})")
    except Exception as e:
        print(f"ERROR: Error in Scoring Engine: {e}")
else:
    print("Skipped: Vectorizer or Profile vectors failed to generate.")

# Step 4: Test Pinecone Connection & Vector Store
print("\n[Step 4/4] Testing Pinecone Vector Store...")
try:
    import vector_store
    print("SUCCESS: Vector Store module imported successfully.")
    print(f"  Connecting to Pinecone index: '{vector_store.index_name}'...")
    
    # Check if index exists and describe it
    desc = vector_store.pc.describe_index(vector_store.index_name)
    print("SUCCESS: Successfully connected to Pinecone!")
    print(f"  Index Host: {desc.host}")
    print(f"  Dimension: {desc.dimension}")
    print(f"  Metric: {desc.metric}")
    print(f"  Status: {desc.status.state}")
    
    if desc.dimension != 384:
        print(f"WARNING: Your Pinecone index has dimension {desc.dimension}, but our sentence-transformers model ('all-MiniLM-L6-v2') outputs dimension 384. This will cause errors when storing vectors!")
    
    print("  Upserting test email to Pinecone...")
    test_id = "test_email_1"
    metadata = {
        "subject": sample_subject,
        "body_preview": sample_body[:200],
        "score": score
    }
    vector_store.save_email(test_id, sample_subject, sample_body, metadata)
    print(f"SUCCESS: Successfully upserted email ID '{test_id}' to Pinecone.")
    
    # Let's clean it up or fetch it to confirm
    print("  Verifying if the record exists in the index...")
    # Fetch from Pinecone
    fetch_response = vector_store.index.fetch(ids=[test_id])
    if test_id in fetch_response.get('vectors', {}):
        print(f"SUCCESS: Verified! Record '{test_id}' retrieved from Pinecone index successfully.")
    else:
        print("WARNING: Record was not found in fetch. It might take a few seconds to index.")

except Exception as e:
    print(f"ERROR: Error in Pinecone / Vector Store: {e}")
    print("\nTroubleshooting Tips:")
    print("1. Make sure your Pinecone API Key in the `.env` file is correct.")
    print("2. Ensure your Pinecone index is named exactly 'emails' (or matches PINECONE_INDEX_NAME).")
    print("3. Ensure the index dimension is set to 384 and metric to 'cosine'.")

print("\n" + "="*60)
print("                        TEST COMPLETE")
print("="*60)
