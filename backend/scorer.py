def score_email(email_vector, profile_vectors):
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    scores = cosine_similarity([email_vector], profile_vectors)[0]
    base_score = float(np.max(scores))
    return base_score  # 0.0 to 1.0