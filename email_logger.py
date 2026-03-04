import pandas as pd
import os
from datetime import datetime

class EmailLogger:
    """
    Logs email analysis results to CSV for history tracking and export
    """
    
    def __init__(self, log_file="email_history.csv"):
        self.log_file = log_file
        self._ensure_log_exists()
    
    def _ensure_log_exists(self):
        """Create log file with headers if it doesn't exist"""
        if not os.path.exists(self.log_file):
            df = pd.DataFrame(columns=[
                'timestamp', 'email_text', 'is_spam', 'importance', 
                'category', 'keywords_used', 'user_feedback'
            ])
            df.to_csv(self.log_file, index=False)
    
    def log_prediction(self, email_text, result, keywords=None):
        """Log a prediction result"""
        new_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'email_text': email_text[:200],  # Truncate long emails
            'is_spam': result['is_spam'],
            'importance': result['importance'],
            'category': result['category'],
            'keywords_used': ','.join(keywords) if keywords else '',
            'user_feedback': ''  # For future feedback
        }
        
        df = pd.read_csv(self.log_file)
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(self.log_file, index=False)
        
        return True
    
    def get_history(self, limit=50):
        """Get recent history"""
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            return df.tail(limit).to_dict('records')
        return []
    
    def get_stats(self):
        """Get statistics from logged data"""
        if not os.path.exists(self.log_file):
            return None
        
        df = pd.read_csv(self.log_file)
        
        if len(df) == 0:
            return None
        
        stats = {
            'total_analyzed': len(df),
            'spam_count': df['is_spam'].sum(),
            'important_count': (df['importance'] == 'Important').sum(),
            'category_distribution': df['category'].value_counts().to_dict()
        }
        
        return stats
    
    def export_report(self, output_file="email_report.csv"):
        """Export full report"""
        if os.path.exists(self.log_file):
            df = pd.read_csv(self.log_file)
            df.to_csv(output_file, index=False)
            return output_file
        return None
    
    def clear_history(self):
        """Clear all history (use with caution)"""
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
            self._ensure_log_exists()
