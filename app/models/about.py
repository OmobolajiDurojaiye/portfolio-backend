from app import db

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bio = db.Column(db.Text, nullable=False, default='Default bio text.')
    spotify_url = db.Column(db.String(255), nullable=True)

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon_name = db.Column(db.String(50), nullable=False) # e.g., 'FaReact' from react-icons

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'icon_name': self.icon_name}

class Tool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon_name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'icon_name': self.icon_name}

class WorkExperience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True) # Optional description
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'company': self.company,
            'duration': self.duration,
            'description': self.description,
            'order': self.order
        }