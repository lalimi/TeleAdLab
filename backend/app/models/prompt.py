from app import db
from datetime import datetime

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_input = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_input': self.user_input,
            'ai_response': self.ai_response,
            'created_at': self.created_at.isoformat()
        }