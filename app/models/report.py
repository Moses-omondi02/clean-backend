from app import db
from datetime import datetime

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'))
    crop_name = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(200))
    image_hash = db.Column(db.String(64), index=True) 
    symptoms_description = db.Column(db.Text)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Analysis results matching frontend
    is_healthy = db.Column(db.Boolean, default=False)
    recommended_treatment = db.Column(db.Text)
    prevention_tips = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'disease_id': self.disease_id,
            'crop_name': self.crop_name,
            'confidence': round(self.confidence * 100, 2),
            'image_path': self.image_path,
            'image_hash': self.image_hash,
            'symptoms_description': self.symptoms_description,
            'location': self.location,
            'created_at': self.created_at.isoformat(),
            'is_healthy': self.is_healthy,
            'recommended_treatment': self.recommended_treatment,
            'prevention_tips': self.prevention_tips,
            'disease_name': self.disease.name if self.disease else None
        }
