# backend/scorer.py

from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
import numpy as np

from vectorizer import vectorize_email, get_profile_vectors
from deadline_detector import extract_deadline


# ── Function from Phase 3 (already written) ──────────────────
def score_email(email_vector, profile_vectors):
    scores = cosine_similarity([email_vector], profile_vectors)[0]
    base_score = float(np.max(scores))
    return base_score  # 0.0 to 1.0


# ── Function 1 from Phase 4 (urgency boost) ──────────────────
def calculate_urgency_boost(deadline_date):
    if deadline_date is None:
        return 0.0
    days_left = (deadline_date - datetime.now()).days
    if days_left < 0:
        return 0.0
    elif days_left <= 1:
        return 0.5
    elif days_left <= 3:
        return 0.35
    elif days_left <= 7:
        return 0.2
    elif days_left <= 30:
        return 0.1
    else:
        return 0.05


# ── Function 2 from Phase 4 (final priority) ─────────────────
def get_final_priority(email):
    vector = vectorize_email(email['subject'], email['body'])
    profile_vecs = get_profile_vectors()

    relevance_score = score_email(vector, profile_vecs)
    deadline = extract_deadline(email['body'])
    urgency_boost = calculate_urgency_boost(deadline)

    final_score = min(1.0, relevance_score + urgency_boost)

    return {
        'score': round(final_score, 3),
        'deadline': deadline,
        'priority': 'HIGH' if final_score > 0.6 else
                    'MEDIUM' if final_score > 0.35 else 'LOW'
    }