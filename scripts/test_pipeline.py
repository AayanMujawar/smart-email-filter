import os
import sys
from datetime import datetime, timedelta

# Reconfigure stdout/stderr to use UTF-8 on Windows to prevent UnicodeEncodeErrors when printing emojis
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure backend directory is in the python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
sys.path.append(backend_dir)


from dotenv import load_dotenv
load_dotenv(os.path.join(current_dir, '..', '.env'))

print("="*60)
print("             SMART EMAIL FILTER PIPELINE TEST")
print("="*60)

# Step 1: Test Vectorizer & Keywords Profile
print("\n[Step 1/6] Testing Email Vectorizer & Profile...")
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
    
    # Test keywords profile
    print(f"  User Keywords Profile: {vectorizer.get_user_profile()}")
    profile_vectors = vectorizer.get_profile_vectors()
    print(f"SUCCESS: Successfully vectorized user profile. Vector count: {len(profile_vectors)}")
except Exception as e:
    print(f"ERROR: Error in Vectorizer: {e}")
    vector = None
    profile_vectors = None

# Step 2: Test Scoring Engine (Relevance)
print("\n[Step 2/6] Testing Scoring Engine (Cosine Similarity)...")
if vector is not None and profile_vectors is not None:
    try:
        import scorer
        relevance_score = scorer.score_email(vector, profile_vectors)
        print("SUCCESS: Scorer module imported successfully.")
        print(f"SUCCESS: Calculated relevance score: {relevance_score:.4f} (0.0 to 1.0 scale)")
        
        # Test with a low-priority email
        junk_subject = "Win a free cruise now!"
        junk_body = "Click this link to claim your reward of one million dollars instantly."
        junk_vector = vectorizer.vectorize_email(junk_subject, junk_body)
        junk_score = scorer.score_email(junk_vector, profile_vectors)
        print(f"SUCCESS: Junk email score: {junk_score:.4f}")
        print(f"  Comparison: Urgent Email Relevance ({relevance_score:.4f}) vs Junk Email Relevance ({junk_score:.4f})")
    except Exception as e:
        print(f"ERROR: Error in Scoring Engine: {e}")
        relevance_score = 0.0
else:
    print("Skipped: Vectorizer or Profile vectors failed to generate.")
    relevance_score = 0.0

# Step 3: Test Deadline Detector
print("\n[Step 3/6] Testing Deadline Detector...")
try:
    import deadline_detector
    print("SUCCESS: Deadline Detector module imported successfully.")
    
    test_cases = [
        ("The deadline for application is 15th July 2026.", "July 15, 2026"),
        ("Please submit your assignment before June 30, 2026.", "June 30, 2026"),
        ("We need this by tomorrow.", "Tomorrow"),
        ("Just a friendly hello, no deadlines here.", "None")
    ]
    
    for text, expected in test_cases:
        parsed = deadline_detector.extract_deadline(text)
        parsed_str = parsed.strftime('%Y-%m-%d') if parsed else "None"
        print(f"  Text: '{text}'")
        print(f"  Parsed: {parsed_str} (Expected/Hint: {expected})")
        
except Exception as e:
    print(f"ERROR: Error in Deadline Detector: {e}")

# Step 4: Test Urgency Booster & Priority Combo
print("\n[Step 4/6] Testing Urgency Booster & Final Priority combo...")
try:
    # Test cases for urgency boost
    now = datetime.now()
    boost_test_cases = [
        (None, 0.0, "No deadline"),
        (now + timedelta(hours=12), 0.5, "Today/Tomorrow"),
        (now + timedelta(days=2), 0.35, "Within 3 days"),
        (now + timedelta(days=5), 0.2, "Within a week"),
        (now + timedelta(days=15), 0.1, "Within a month"),
        (now + timedelta(days=45), 0.05, "Future deadline")
    ]
    
    print("  Testing Urgency Boost calculation:")
    for dt, expected_boost, desc in boost_test_cases:
        boost = scorer.calculate_urgency_boost(dt)
        print(f"    {desc} ({dt.strftime('%Y-%m-%d') if dt else 'None'}): Calculated Boost = {boost} (Expected: {expected_boost})")
        
    # Test final priority on a sample email
    sample_email = {
        'subject': "Action Required: Fee payment last date",
        'body': "Please pay your fees by tomorrow or a late fine will be charged."
    }
    print(f"\n  Scoring email: '{sample_email['subject']}'")
    result = scorer.get_final_priority(sample_email)
    print(f"  Result: Score = {result['score']}, Deadline = {result['deadline']}, Priority = {result['priority']}")
    
except Exception as e:
    print(f"ERROR: Error in Urgency Boost/Priority: {e}")

# Step 5: Test Pinecone Connection & Vector Store
print("\n[Step 5/6] Testing Pinecone Connection & Vector Store...")
try:
    import vector_store
    print("SUCCESS: Vector Store module imported successfully.")
    
    # Check if we have API key
    if not os.getenv("PINECONE_API_KEY") or os.getenv("PINECONE_API_KEY") == "your_pinecone_api_key_here":
        print("WARNING: Pinecone API Key is not set or is using placeholder. Skipping Pinecone connection test.")
    else:
        print(f"  Connecting to Pinecone index: '{vector_store.index_name}'...")
        desc = vector_store.pc.describe_index(vector_store.index_name)
        print("SUCCESS: Successfully connected to Pinecone!")
        print(f"  Index Host: {desc.host}")
        print(f"  Dimension: {desc.dimension}")
        print(f"  Metric: {desc.metric}")
        print(f"  Status: {desc.status.state}")
        
        if desc.dimension != 384:
            print(f"WARNING: Pinecone index has dimension {desc.dimension}, but sentence-transformers model outputs 384. This will error during upsert.")
            
        print("  Upserting test email to Pinecone...")
        test_id = "test_email_pipeline"
        metadata = {
            "subject": sample_subject,
            "body_preview": sample_body[:200],
            "score": float(relevance_score) if relevance_score else 0.0
        }
        vector_store.save_email(test_id, sample_subject, sample_body, metadata)
        print(f"SUCCESS: Successfully upserted email ID '{test_id}' to Pinecone.")
        
        # Verify
        print("  Verifying records...")
        fetch_response = vector_store.index.fetch(ids=[test_id])
        if test_id in fetch_response.get('vectors', {}):
            print(f"SUCCESS: Verified! Record '{test_id}' retrieved from Pinecone successfully.")
        else:
            print("WARNING: Record was not found in fetch. It might take a few seconds to index.")
except Exception as e:
    print(f"ERROR: Error in Pinecone / Vector Store: {e}")

# Step 6: Test Notifier Formatting & Dry-run Alerts
print("\n[Step 6/6] Testing Notifier Formatting & Configuration...")
try:
    import notifier
    print("SUCCESS: Notifier module imported successfully.")
    
    print("  Checking Notification credentials config in .env:")
    token_display = "Configured" if notifier.TELEGRAM_BOT_TOKEN else "MISSING"
    print(f"    Telegram Bot Token: {token_display}")
    print(f"    Telegram Chat ID: {'Configured' if notifier.CHAT_ID else 'MISSING'}")
    print(f"    Sender Email: {notifier.SENDER_EMAIL or 'MISSING'}")
    
    # Format a dummy alert message
    dummy_important = [
        {
            'subject': "College Registration Deadline",
            'from': "admissions@college.edu",
            'deadline': datetime.now() + timedelta(days=1),
            'priority': "HIGH",
            'score': 0.85
        },
        {
            'subject': "Internship Offer Letter Received",
            'from': "careers@techcorp.com",
            'deadline': datetime.now() + timedelta(days=5),
            'priority': "HIGH",
            'score': 0.78
        }
    ]
    
    formatted_msg = notifier.format_alert(dummy_important)
    print("\n  Sample Formatted Telegram Alert Message:")
    print("-" * 45)
    print(formatted_msg.strip())
    print("-" * 45)
    
except Exception as e:
    print(f"ERROR: Error in Notifier verification: {e}")

print("\n" + "="*60)
print("                        TEST COMPLETE")
print("="*60)
