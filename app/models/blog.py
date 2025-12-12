from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import MEDIUMTEXT

class PostReadlistOrder(db.Model):
    __tablename__ = 'posts_readlists'
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    readlist_id = db.Column(db.Integer, db.ForeignKey('readlist.id'), primary_key=True)
    post_order = db.Column(db.Integer, default=0)

    post = db.relationship('Post', back_populates='readlist_associations')
    readlist = db.relationship('Readlist', back_populates='post_associations')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), nullable=False, default='#ffffff')
    posts = db.relationship('Post', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug, 'color': self.color}

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, unique=True)
    slug = db.Column(db.String(150), nullable=False, unique=True)
    content = db.Column(MEDIUMTEXT, nullable=False)
    excerpt = db.Column(db.String(300), nullable=True)
    author = db.Column(db.String(100), default="Bolaji")
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_url = db.Column(db.String(200), nullable=True)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    view_count = db.Column(db.Integer, default=0)

    readlist_associations = db.relationship('PostReadlistOrder', back_populates='post')

    def to_dict(self, include_readlists=False):
        data = {
            'id': self.id, 'title': self.title, 'slug': self.slug, 'content': self.content,
            'excerpt': self.excerpt, 'author': self.author, 'date_posted': self.date_posted.isoformat(),
            'image_url': self.image_url, 'is_featured': self.is_featured,
            'category': self.category.to_dict() if self.category else None, 'view_count': self.view_count
        }
        if include_readlists:
            data['readlists'] = [assoc.readlist_id for assoc in self.readlist_associations]
        return data

class Readlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(200), nullable=True)
    order = db.Column(db.Integer, default=0)

    post_associations = db.relationship('PostReadlistOrder', back_populates='readlist', cascade="all, delete-orphan")
    
    @property
    def posts(self):
        return [assoc.post for assoc in sorted(self.post_associations, key=lambda x: x.post_order)]

    def to_dict(self, include_posts=False):
        data = {
            'id': self.id, 'name': self.name, 'slug': self.slug, 'description': self.description,
            'image_url': self.image_url, 'order': self.order
        }
        if include_posts:
            data['posts'] = [p.to_dict() for p in self.posts]
        return data