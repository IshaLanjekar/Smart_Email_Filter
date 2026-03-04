# Email Intelligence Filter

A smart email spam detection and categorization system with keyword-based filtering and Gmail integration.

## ✨ Features

### 1. **3-Stage Email Analysis**
- **Stage 1:** Spam Detection (97.2% accuracy)
- **Stage 2:** Keyword Importance Filtering (user-defined)
- **Stage 3:** Category Classification (Work / Promotional / Academic)

### 2. **Email History & Logging** ✅ NEW
- Automatic logging of all analyzed emails to CSV
- View analysis history in sidebar
- Export full reports with timestamps
- Track statistics (total analyzed, spam count, important count)

### 3. **Manual Labeling Interface** ✅ NEW
- Label emails to improve training data
- Track labeling progress (goal: 500+ emails)
- Address the "other" category issue (4,382/4,825 emails)
- Export labeled data for retraining

### 4. **Gmail Integration** ✅ NEW
- Connect to Gmail via OAuth2
- Fetch unread emails automatically
- Auto-filter spam and mark important emails
- Apply category labels to Gmail

---

## 🚀 Quick Start

### Installation
```bash
cd "c:\Users\isha vijay lanjekar\email spam project"
pip install -r requirements.txt
```

### Train Models
```bash
python train_model.py
```

### Run App
```bash
streamlit run app.py --server.port 8501
```

Open: http://localhost:8501

---

## 📊 Usage Guide

### Tab 1: Analyze Email
1. Set your keywords in sidebar (e.g., "urgent", "meeting", "boss")
2. Paste email text
3. Click "Analyze Email"
4. View results: Spam? | Importance | Category
5. Provide feedback if prediction is incorrect

### Tab 2: Label Email (Training)
1. Paste email text or come from incorrect prediction
2. Select spam/ham
3. Choose category (work/promotional/academic/other)
4. Click "Save Label"
5. Track progress toward 500+ labels

### Tab 3: Gmail Auto-Filter
1. Click "Setup Instructions" in sidebar for OAuth setup
2. Authenticate with Gmail
3. Fetch recent emails
4. Auto-filter spam and mark important emails

---

## 📁 File Structure

```
email spam project/
├── app.py                      # Main Streamlit UI
├── train_model.py              # Model training (2-stage)
├── predict.py                  # Prediction logic
├── email_logger.py             # History & export ✅ NEW
├── email_labeler.py            # Manual labeling ✅ NEW
├── gmail_integration.py        # Gmail API ✅ NEW
├── test_emails.py              # Test cases
├── spam.csv                    # Training dataset
├── spam_model.pkl              # Trained spam model
├── vectorizer_spam.pkl         # TF-IDF vectorizer
├── category_model.pkl          # Category classifier
├── email_history.csv           # Logged predictions ✅ NEW
├── labeled_emails.csv          # Manual labels ✅ NEW
└── requirements.txt            # Dependencies
```

---

## 🔧 Gmail Integration Setup

### Step 1: Install Gmail Libraries
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Step 2: Enable Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable "Gmail API"
4. Create OAuth 2.0 credentials (Desktop App)
5. Download as `credentials.json`

### Step 3: Place Credentials
```
c:\Users\isha vijay lanjekar\email spam project\credentials.json
```

### Step 4: Authenticate
In the app, go to "Gmail Auto-Filter" tab and click "Authenticate Gmail".

---

## 📈 Model Performance

### Spam Detection (Stage 1)
```
Accuracy: 97.22%
Precision (spam): 0.99
Recall (spam): 0.80
F1-Score (spam): 0.89
```

### Category Classification (Stage 3)
```
Accuracy: 65.17% (baseline)
Work: 210 samples
Promotional: 143 samples
Academic: 90 samples
Other: 4,382 samples (needs labeling!)
```

**Solution:** Use manual labeling interface to add 500+ labeled emails.

---

## 🎯 Next Steps

### Improve Category Accuracy
1. Go to "Label Email (Training)" tab
2. Label 500+ emails with correct categories
3. Retrain model: `python train_model.py`

### Export & Analyze
1. Click "Export Full Report" in sidebar
2. Analyze patterns in CSV
3. Identify which keywords work best

### Automate Gmail
1. Complete Gmail setup
2. Run daily to auto-filter incoming emails
3. Build custom filters based on analysis

---

## 🛠️ Advanced Features

### Retrain with Custom Data
```python
# After labeling 500+ emails
from email_labeler import EmailLabeler

labeler = EmailLabeler()
labeler.export_for_training("training_data.csv")

# Then update train_model.py to use this data
```

### Export Analysis Reports
```python
from email_logger import EmailLogger

logger = EmailLogger()
stats = logger.get_stats()
logger.export_report("monthly_report.csv")
```

### Custom Gmail Filters
```python
from gmail_integration import GmailIntegration
from predict import predict_email

gmail = GmailIntegration()
gmail.authenticate()

emails = gmail.get_recent_emails(max_results=50)
for email in emails:
    result = predict_email(email['body'], your_keywords)
    
    if result['is_spam']:
        gmail.move_to_spam(email['id'])
    elif result['importance'] == 'Important':
        gmail.mark_important(email['id'])
    
    # Apply category label
    gmail.apply_label(email['id'], result['category'])
```

---

## 📝 Test Examples

Run test suite:
```bash
python test_emails.py
```

5 test cases included:
1. Spam (prize scam)
2. Work + Keywords matched
3. Work + No keywords
4. Promotional
5. Academic

---

## 🐛 Troubleshooting

### Gmail Authentication Error
- Make sure `credentials.json` is in project folder
- Check OAuth consent screen is configured
- Enable Gmail API in Cloud Console

### Model Not Loading
```bash
python train_model.py  # Retrain models
```

### Import Errors
```bash
pip install -r requirements.txt
```

---

## 📧 Support

For issues or improvements, check:
- Email history logs: `email_history.csv`
- Labeled data: `labeled_emails.csv`
- Training outputs: Console logs from `train_model.py`

---

## 🎉 Success Metrics

- ✅ Spam detection: 97.2% accuracy
- ✅ Email history: Auto-logged to CSV
- ✅ Manual labeling: Track progress to 500+
- ✅ Gmail integration: OAuth2 ready
- 🎯 Next: Improve category accuracy from 65% → 85%+

**Start using the app and label emails to improve model performance!** 🚀
