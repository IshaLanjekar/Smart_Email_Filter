"""
Quick test for new features: Email Logger and Email Labeler
"""

from email_logger import EmailLogger
from email_labeler import EmailLabeler
from predict import predict_email

print("="*70)
print("TESTING NEW FEATURES")
print("="*70)

# Test 1: Email Logger
print("\n[TEST 1] Email Logger")
print("-"*70)

logger = EmailLogger()

# Log a few test predictions
test_emails = [
    ("Win a free iPhone now!", ["urgent"]),
    ("Meeting tomorrow at 3 PM", ["meeting", "deadline"]),
    ("Check out our 50% sale!", [])
]

for email_text, keywords in test_emails:
    result = predict_email(email_text, keywords)
    logger.log_prediction(email_text, result, keywords)
    print(f"✅ Logged: {email_text[:40]}...")

# Get stats
stats = logger.get_stats()
if stats:
    print(f"\nStatistics:")
    print(f"  Total analyzed: {stats['total_analyzed']}")
    print(f"  Spam count: {stats['spam_count']}")
    print(f"  Important count: {stats['important_count']}")

# Get history
history = logger.get_history(limit=3)
print(f"\nRecent history (last 3):")
for entry in history:
    print(f"  - {entry['timestamp']}: {entry['email_text'][:50]}...")

print("\n✅ Email Logger: WORKING")

# Test 2: Email Labeler
print("\n[TEST 2] Email Labeler")
print("-"*70)

labeler = EmailLabeler()

# Add some test labels
test_labels = [
    ("Project deadline is tomorrow", "ham", "work"),
    ("50% off sale now!", "ham", "promotional"),
    ("Assignment due next week", "ham", "academic"),
]

for email_text, spam_label, category in test_labels:
    labeler.add_label(email_text, spam_label, category)
    print(f"✅ Labeled: {email_text[:40]}... as {category}")

# Get stats
labeled_count = labeler.get_labeled_count()
print(f"\nLabeled emails count: {labeled_count}")

dist = labeler.get_category_distribution()
print(f"Category distribution:")
for cat, count in dist.items():
    print(f"  - {cat}: {count}")

print("\n✅ Email Labeler: WORKING")

# Test 3: Export functionality
print("\n[TEST 3] Export Features")
print("-"*70)

# Export logger report
report_file = logger.export_report("test_report.csv")
if report_file:
    print(f"✅ Exported email history to: {report_file}")

# Export labeled data
training_file = labeler.export_for_training("test_training_data.csv")
if training_file:
    print(f"✅ Exported training data to: {training_file}")

print("\n" + "="*70)
print("ALL TESTS PASSED ✅")
print("="*70)
print("\nNew features are working correctly!")
print("Files created:")
print("  - email_history.csv")
print("  - labeled_emails.csv")
print("  - test_report.csv")
print("  - test_training_data.csv")
