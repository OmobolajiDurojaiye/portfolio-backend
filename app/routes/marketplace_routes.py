from flask import Blueprint, jsonify, request
from app.models.product import Product, ProductCategory
from app.models.order import ProductOrder
from app import db, mail
from flask_mail import Message
from flask_jwt_extended import jwt_required
import os

marketplace_bp = Blueprint('marketplace_bp', __name__)

# --- Public Routes ---
@marketplace_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.order_by(Product.id.desc()).all()
    categories = ProductCategory.query.order_by(ProductCategory.name.asc()).all()
    return jsonify({
        'products': [p.to_dict() for p in products],
        'categories': [c.to_dict() for c in categories]
    })

@marketplace_bp.route('/products/<string:slug>', methods=['GET'])
def get_product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    return jsonify(product.to_dict())

@marketplace_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    product = Product.query.get_or_404(data['product_id'])
    
    new_order = ProductOrder(
        customer_name=data['name'], customer_email=data['email'],
        customer_phone=data.get('phone'), product_id=product.id
    )
    db.session.add(new_order)
    db.session.commit()
    
    try:
        msg_admin = Message(subject=f"New Marketplace Order: {product.name}", recipients=[os.environ.get('MAIL_FROM')], body=f"You have a new order inquiry for '{product.name}'.\n\nCustomer Details:\nName: {data['name']}\nEmail: {data['email']}\nPhone: {data.get('phone', 'N/A')}\n\nYou can view this order in your admin dashboard.")
        mail.send(msg_admin)
        msg_customer = Message(subject="Your Order Inquiry has been received", recipients=[data['email']], body=f"Hi {data['name']},\n\nThank you for your interest in '{product.name}'.\n\nYour inquiry has been received, and I will get back to you shortly to discuss the next steps.\n\nBest,\nBolaji")
        mail.send(msg_customer)
    except Exception as e:
        print(f"Mail sending failed: {e}")

    return jsonify({'message': 'Order submitted successfully!'}), 201

# --- Admin Routes ---
@marketplace_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def admin_get_stats():
    sold_products = Product.query.filter_by(is_sold=True).all()
    total_revenue = sum(p.price for p in sold_products)
    apps_sold = len(sold_products)
    return jsonify({'total_revenue': total_revenue, 'apps_sold': apps_sold})

@marketplace_bp.route('/admin/orders', methods=['GET'])
@jwt_required()
def admin_get_orders():
    orders = ProductOrder.query.order_by(ProductOrder.order_date.desc()).all()
    return jsonify([o.to_dict() for o in orders])

@marketplace_bp.route('/admin/products', methods=['GET'])
@jwt_required()
def admin_get_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([p.to_dict() for p in products])

def generate_slug(name):
    return name.lower().replace(' ', '-').replace('[^a-z0-9-]', '')

@marketplace_bp.route('/admin/products', methods=['POST'])
@jwt_required()
def admin_add_product():
    data = request.get_json()
    new_product = Product(
        name=data['name'], slug=generate_slug(data['name']), subtitle=data.get('subtitle'),
        description=data['description'], features=data.get('features'), price=float(data['price']),
        image_url=data.get('image_url'), gallery_images=data.get('gallery_images'),
        product_url=data.get('product_url'), demo_url=data.get('demo_url'),
        tags=data.get('tags'), is_sold=data.get('is_sold', False),
        category_id=data.get('category_id') if data.get('category_id') else None
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

@marketplace_bp.route('/admin/products/<int:prod_id>', methods=['PUT'])
@jwt_required()
def admin_update_product(prod_id):
    product = Product.query.get_or_404(prod_id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.slug = generate_slug(data.get('name', product.name))
    product.subtitle = data.get('subtitle', product.subtitle)
    product.description = data.get('description', product.description)
    product.features = data.get('features', product.features)
    product.price = float(data.get('price', product.price))
    product.image_url = data.get('image_url', product.image_url)
    product.gallery_images = data.get('gallery_images', product.gallery_images)
    product.product_url = data.get('product_url', product.product_url)
    product.demo_url = data.get('demo_url', product.demo_url)
    product.tags = data.get('tags', product.tags)
    product.is_sold = data.get('is_sold', product.is_sold)
    product.category_id = data.get('category_id') if data.get('category_id') else None
    db.session.commit()
    return jsonify(product.to_dict())

@marketplace_bp.route('/admin/products/<int:prod_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_product(prod_id):
    product = Product.query.get_or_404(prod_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

@marketplace_bp.route('/admin/categories', methods=['GET'])
@jwt_required()
def admin_get_categories():
    categories = ProductCategory.query.order_by(ProductCategory.name.asc()).all()
    return jsonify([c.to_dict() for c in categories])

@marketplace_bp.route('/admin/categories', methods=['POST'])
@jwt_required()
def admin_add_category():
    data = request.get_json()
    new_cat = ProductCategory(name=data['name'], slug=data['slug'])
    db.session.add(new_cat)
    db.session.commit()
    return jsonify(new_cat.to_dict()), 201

@marketplace_bp.route('/admin/categories/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_category(cat_id):
    category = ProductCategory.query.get_or_404(cat_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted'})