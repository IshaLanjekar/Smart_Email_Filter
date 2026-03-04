"""
5 Test Email Examples - Different Outputs
"""
from predict import predict_email

# Test emails
test_cases = [
    {
        "name": "Email 1: SPAM - Prize Winner",
        "text": "Congratulations! You have won $1,000,000! Click here to claim your prize now. Limited time offer!",
        "keywords": ["urgent", "meeting", "deadline"]
    },
    {
        "name": "Email 2: WORK - With Keywords Match",
        "text": "Hi team, we have a meeting tomorrow at 2 PM to discuss the project deadline and budget allocation. Please come prepared.",
        "keywords": ["meeting", "deadline", "urgent"]
    },
    {
        "name": "Email 3: WORK - No Keywords Match",
        "text": "The quarterly report has been finalized and is ready for review. Please check the attached document for details.",
        "keywords": ["urgent", "sale", "discount"]
    },
    {
        "name": "Email 4: PROMOTIONAL - Discount Offer",
        "text": "Flash Sale! Get 50% off all items this weekend. Use code SAVE50 at checkout. Shop now before stock runs out!",
        "keywords": ["meeting", "exam", "assignment"]
    },
    {
        "name": "Email 5: ACADEMIC - Course Assignment",
        "text": "Dear Student, Your assignment submission for the course is due next Friday. Please submit via the university portal before the deadline.",
        "keywords": ["deadline", "urgent", "submission"]
    }
]

print("="*70)
print("5 EMAIL TEST CASES - DIFFERENT OUTPUTS")
print("="*70)

for i, case in enumerate(test_cases, 1):
    print(f"\n{case['name']}")
    print("-"*70)
    print(f"Email: {case['text'][:80]}...")
    print(f"Keywords set: {case['keywords']}")
    print()
    
    result = predict_email(case['text'], case['keywords'])
    
    print(f"Is Spam:   {result['is_spam']}")
    print(f"Importance: {result['importance']}")
    print(f"Category:   {result['category']}")
    print(f"Message:    {result['message']}")
    print()

print("="*70)
print("TEST COMPLETE")
print("="*70)
