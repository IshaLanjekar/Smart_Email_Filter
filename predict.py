import pickle
import re
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords', quiet=True)

# 🔹 Load models
spam_model = pickle.load(open("spam_model.pkl", "rb"))
vectorizer_spam = pickle.load(open("vectorizer_spam.pkl", "rb"))
category_model = pickle.load(open("category_model.pkl", "rb"))

stop_words = set(stopwords.words('english'))

# 🔹 Clean function (same as training)
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# ============================================================
# STAGE 1: SPAM DETECTION
# ============================================================
def is_spam(email_text):
    cleaned = clean_text(email_text)
    vec = vectorizer_spam.transform([cleaned])
    prediction = spam_model.predict(vec)[0]
    return prediction == 1

# ============================================================
# STAGE 2: IMPORTANCE (KEYWORD-BASED)
# ============================================================
def check_importance(email_text, user_keywords=None):
    """
    If user keywords provided and ANY match → Important
    If no keywords provided or NO match → Not Important
    """
    if not user_keywords or len(user_keywords) == 0:
        return "Not Important"
    
    email_lower = email_text.lower()
    for keyword in user_keywords:
        if keyword.lower() in email_lower:
            return "Important"
    
    return "Not Important"

# ============================================================
# STAGE 3: CATEGORY CLASSIFICATION
# ============================================================
def classify_category(email_text):
    """
    Classify non-spam email into: Work, Promotional, Academic
    """
    cleaned = clean_text(email_text)
    vec = vectorizer_spam.transform([cleaned])
    category = category_model.predict(vec)[0]
    
    # Map internal names to display names
    category_map = {
        'work': 'Work',
        'promotional': 'Promotional',
        'academic': 'Academic'
    }
    
    return category_map.get(category, category)

# ============================================================
# MAIN PREDICTION FUNCTION (3-stage pipeline)
# ============================================================
def predict_email(email_text, user_keywords=None):
    """
    Returns dict with:
    - is_spam: True/False
    - importance: Important / Not Important (only if not spam)
    - category: Work / Promotional / Academic (only if not spam)
    - message: Human-readable result
    """
    
    # Stage 1: Check spam
    spam_flag = is_spam(email_text)
    
    if spam_flag:
        return {
            'is_spam': True,
            'importance': None,
            'category': None,
            'message': '🚨 SPAM DETECTED'
        }
    
    # Stage 2: Check importance (if not spam)
    importance = check_importance(email_text, user_keywords)
    
    # Stage 3: Classify category (if not spam)
    category = classify_category(email_text)
    
    return {
        'is_spam': False,
        'importance': importance,
        'category': category,
        'message': f'✅ Not Spam | {category} | {importance}'
    }

# ============================================================
# Test example
# ============================================================
if __name__ == "__main__":
    print("Testing 3-stage prediction...\n")
    
    # Test 1: Spam
    email1 = "Congratulations! You won a free iPhone. Claim now!"
    result1 = predict_email(email1, ['iphone', 'free'])
    print(f"Test 1 (Spam):\n{result1}\n")
    
    # Test 2: Ham with keywords
    email2 = "Hi, we have a meeting tomorrow at 3 PM to discuss the project deadline."
    result2 = predict_email(email2, ['meeting', 'deadline'])
    print(f"Test 2 (Ham + Keywords matched):\n{result2}\n")
    
    # Test 3: Ham without keywords
    email3 = "Check out our latest promotion: 50% off all items!"
    result3 = predict_email(email3, ['meeting', 'exam'])
    print(f"Test 3 (Ham + No keywords matched):\n{result3}\n")