from app import db

class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    slug = db.Column(db.String(50), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'slug': self.slug}

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    subtitle = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=False)
    features = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    gallery_images = db.Column(db.Text, nullable=True)
    product_url = db.Column(db.String(200), nullable=False)
    demo_url = db.Column(db.String(200), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    is_sold = db.Column(db.Boolean, default=False) # New field
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'subtitle': self.subtitle,
            'description': self.description,
            'features': self.features.split('\n') if self.features else [],
            'price': self.price,
            'image_url': self.image_url,
            'gallery_images': self.gallery_images.split(',') if self.gallery_images else [],
            'product_url': self.product_url,
            'demo_url': self.demo_url,
            'tags': self.tags.split(',') if self.tags else [],
            'rating': self.rating,
            'rating_count': self.rating_count,
            'is_sold': self.is_sold,
            'category': self.category.to_dict() if self.category else None
        }