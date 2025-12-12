from app import db

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(255), nullable=True) # New field
    tech_stack = db.Column(db.String(200), nullable=True)
    tools = db.Column(db.String(200), nullable=True)
    live_url = db.Column(db.String(200), nullable=True)
    github_url = db.Column(db.String(200), nullable=True)
    case_study_url = db.Column(db.String(200), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    duration = db.Column(db.String(100), nullable=True)
    cost = db.Column(db.Float, nullable=True) # Restored
    collaborators = db.Column(db.String(200), nullable=True) # Restored
    order = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'role': self.role,
            'tech_stack': self.tech_stack.split(',') if self.tech_stack else [],
            'tools': self.tools.split(',') if self.tools else [],
            'live_url': self.live_url,
            'github_url': self.github_url,
            'case_study_url': self.case_study_url,
            'image_url': self.image_url,
            'duration': self.duration,
            'cost': self.cost,
            'collaborators': self.collaborators,
            'order': self.order
        }