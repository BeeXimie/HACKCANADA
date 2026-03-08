from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    auth0_sub = db.Column(db.String(128), unique=True, nullable=False)
    
    # Profile Fields
    institution = db.Column(db.String(255))
    major = db.Column(db.String(255))
    degree = db.Column(db.String(128))
    gpa = db.Column(db.String(64))
    grad_year = db.Column(db.Integer)
    enrollment = db.Column(db.String(64))
    income_bracket = db.Column(db.String(128))
    first_gen = db.Column(db.String(64))
    fafsa = db.Column(db.String(64))
    aid_amount = db.Column(db.Integer)
    ethnicity = db.Column(db.String(128))
    gender = db.Column(db.String(64))
    location = db.Column(db.String(255))
    disability = db.Column(db.String(128))
    veteran = db.Column(db.String(128))
    career_goals = db.Column(db.Text)
    interests = db.Column(db.Text) # Stored as comma-separated
    year_of_study = db.Column(db.String(128))
    
    # Experiences stored as JSON string
    experiences_json = db.Column(db.Text, default='[]')
    
    # Document tracking
    resume_uploaded = db.Column(db.Boolean, default=False)
    resume_filename = db.Column(db.String(255))
    transcript_uploaded = db.Column(db.Boolean, default=False)
    transcript_filename = db.Column(db.String(255))

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        # Special handling for JSON fields
        try:
            data['experiences'] = json.loads(self.experiences_json)
        except:
            data['experiences'] = []
        return data

    def from_dict(self, data):
        for k, v in data.items():
            if hasattr(self, k):
                # Type conversion for integers
                if isinstance(getattr(User, k).type, db.Integer):
                    try:
                        v = int(v) if v else 0
                    except:
                        v = 0
                # Handle list to string for interests
                if k == 'interests' and isinstance(v, list):
                    v = ', '.join(v)
                setattr(self, k, v)
            elif k == 'experiences':
                if isinstance(v, str):
                    self.experiences_json = v
                else:
                    self.experiences_json = json.dumps(v)
