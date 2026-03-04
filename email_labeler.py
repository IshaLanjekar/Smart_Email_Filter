import pandas as pd
import os

class EmailLabeler:
    """
    Manual labeling system to improve category training data
    """
    
    def __init__(self, labeled_file="labeled_emails.csv"):
        self.labeled_file = labeled_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create labeled file with headers if it doesn't exist"""
        if not os.path.exists(self.labeled_file):
            df = pd.DataFrame(columns=[
                'email_text', 'spam_label', 'category_label', 'timestamp'
            ])
            df.to_csv(self.labeled_file, index=False)
    
    def add_label(self, email_text, spam_label, category_label):
        """
        Add a manually labeled email
        
        Args:
            email_text: The email content
            spam_label: 'spam' or 'ham'
            category_label: 'work', 'promotional', 'academic', or 'other'
        """
        from datetime import datetime
        
        new_entry = {
            'email_text': email_text,
            'spam_label': spam_label,
            'category_label': category_label,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        df = pd.read_csv(self.labeled_file)
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(self.labeled_file, index=False)
        
        return True
    
    def get_labeled_count(self):
        """Get count of labeled emails"""
        if os.path.exists(self.labeled_file):
            df = pd.read_csv(self.labeled_file)
            return len(df)
        return 0
    
    def get_category_distribution(self):
        """Get distribution of labeled categories"""
        if os.path.exists(self.labeled_file):
            df = pd.read_csv(self.labeled_file)
            if len(df) > 0:
                return df['category_label'].value_counts().to_dict()
        return {}
    
    def export_for_training(self, output_file="training_data.csv"):
        """
        Export labeled data in format suitable for model training
        """
        if os.path.exists(self.labeled_file):
            df = pd.read_csv(self.labeled_file)
            
            # Convert to training format
            df['label'] = df['spam_label'].map({'spam': 1, 'ham': 0})
            df['text'] = df['email_text']
            df['category'] = df['category_label']
            
            # Save
            df[['text', 'label', 'category']].to_csv(output_file, index=False)
            return output_file
        return None
