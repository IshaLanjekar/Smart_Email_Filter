import pandas as pd
import re
import nltk
import pickle
from nltk.corpus import stopwords
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

nltk.download('stopwords', quiet=True)

print("="*60)
print("Starting 2-Stage Model Training")
print("="*60)

# 🔹 Text cleaning function
stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# ============================================================
# STAGE 1: SPAM DETECTION MODEL
# ============================================================
print("\n[STAGE 1] Training Spam Detector...")
print("-"*60)

df = pd.read_csv("spam.csv", encoding='latin-1')
df = df[['v1', 'v2']]
df.columns = ['label', 'text']
df['label'] = df['label'].map({'ham': 0, 'spam': 1})
df = df.dropna(subset=['text', 'label'])

print(f"Dataset: {len(df)} emails ({df['label'].value_counts().to_dict()})")

# Clean text
df['clean_text'] = df['text'].apply(clean_text)

# Vectorize
vectorizer_spam = TfidfVectorizer(max_features=5000)
X_spam = vectorizer_spam.fit_transform(df['clean_text'])
y_spam = df['label']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X_spam, y_spam, test_size=0.2, random_state=42
)

# Train model
spam_model = MultinomialNB()
spam_model.fit(X_train, y_train)

# Evaluate
y_pred = spam_model.predict(X_test)
accuracy_spam = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred, target_names=['ham', 'spam'])

print(f"\nAccuracy: {accuracy_spam:.4f}")
print("Confusion Matrix:")
print(cm)
print("\nClassification Report:")
print(report)

# Save Stage 1 artifacts
pickle.dump(spam_model, open("spam_model.pkl", "wb"))
pickle.dump(vectorizer_spam, open("vectorizer_spam.pkl", "wb"))
print("\n✅ Stage 1 models saved: spam_model.pkl, vectorizer_spam.pkl")

# ============================================================
# STAGE 3: CATEGORY CLASSIFIER (Work / Promotional / Academic)
# ============================================================
print("\n[STAGE 3] Training Category Classifier...")
print("-"*60)

# Filter only ham (non-spam) emails
df_ham = df[df['label'] == 0].copy()
print(f"Non-spam emails for classification: {len(df_ham)}")

# Define category keywords
work_keywords = ['meeting', 'project', 'deadline', 'report', 'presentation', 
                 'client', 'manager', 'team', 'work', 'task', 'assigned', 'schedule']
promo_keywords = ['discount', 'offer', 'sale', 'promotion', 'coupon', 'limited', 
                  'free', 'deal', 'purchase', 'order', 'shop', 'exclusive']
academic_keywords = ['assignment', 'exam', 'course', 'submission', 'university', 
                     'lecture', 'grade', 'student', 'professor', 'homework', 'class', 'semester']

# Auto-label ham emails by keywords
def assign_category(text):
    text_lower = text.lower()
    
    work_score = sum(1 for kw in work_keywords if kw in text_lower)
    promo_score = sum(1 for kw in promo_keywords if kw in text_lower)
    academic_score = sum(1 for kw in academic_keywords if kw in text_lower)
    
    max_score = max(work_score, promo_score, academic_score)
    
    if max_score == 0:
        return 'other'  # No strong category match
    if work_score == max_score:
        return 'work'
    elif promo_score == max_score:
        return 'promotional'
    else:
        return 'academic'

df_ham['category'] = df_ham['text'].apply(assign_category)

print(f"\nCategory distribution:")
print(df_ham['category'].value_counts())

# Prepare data for category model
X_category = vectorizer_spam.transform(df_ham['clean_text'])  # Reuse spam vectorizer
y_category = df_ham['category']

# Filter out 'other' category for cleaner training
df_ham_filtered = df_ham[df_ham['category'] != 'other'].copy()
X_category = vectorizer_spam.transform(df_ham_filtered['clean_text'])
y_category = df_ham_filtered['category']

print(f"Filtered emails (excluding 'other'): {len(df_ham_filtered)}")

# Train-test split
X_train_cat, X_test_cat, y_train_cat, y_test_cat = train_test_split(
    X_category, y_category, test_size=0.2, random_state=42, stratify=y_category
)

# Train category model
category_model = MultinomialNB()
category_model.fit(X_train_cat, y_train_cat)

# Evaluate
y_pred_cat = category_model.predict(X_test_cat)
accuracy_cat = accuracy_score(y_test_cat, y_pred_cat)
report_cat = classification_report(y_test_cat, y_pred_cat)

print(f"\nCategory Model Accuracy: {accuracy_cat:.4f}")
print("Classification Report:")
print(report_cat)

# Save Stage 3 artifacts
pickle.dump(category_model, open("category_model.pkl", "wb"))
print("\n✅ Stage 3 model saved: category_model.pkl")

# ============================================================
# Summary
# ============================================================
print("\n" + "="*60)
print("Training Complete!")
print("="*60)
print(f"Stage 1 (Spam Detection): {accuracy_spam:.4f}")
print(f"Stage 3 (Category): {accuracy_cat:.4f}")
print("\nSaved artifacts:")
print("  - spam_model.pkl")
print("  - vectorizer_spam.pkl")
print("  - category_model.pkl")