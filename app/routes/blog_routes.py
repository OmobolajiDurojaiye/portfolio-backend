from flask import Blueprint, jsonify, request, current_app
from app.models.blog import Post, Readlist, Category, PostReadlistOrder
from app import db
from flask_jwt_extended import jwt_required
from sqlalchemy import func
import random
import os
from werkzeug.utils import secure_filename
import time

blog_bp = Blueprint('blog_bp', __name__)

# --- Public Routes ---
@blog_bp.route('/home-data', methods=['GET'])
def get_blog_home_data():
    page = request.args.get('page', 1, type=int)
    per_page = 10 
    featured_post = Post.query.filter_by(is_featured=True).order_by(Post.date_posted.desc()).first()
    posts_query = Post.query.filter(Post.is_featured == False, Post.id != (featured_post.id if featured_post else None)).order_by(Post.date_posted.desc())
    paginated_posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    readlists = Readlist.query.order_by(Readlist.order.asc()).all()
    
    return jsonify({
        'featuredPost': featured_post.to_dict() if featured_post else None,
        'posts': [post.to_dict() for post in paginated_posts.items],
        'readlists': [readlist.to_dict() for readlist in readlists],
        'pagination': { 'page': paginated_posts.page, 'totalPages': paginated_posts.pages, 'hasNext': paginated_posts.has_next, 'hasPrev': paginated_posts.has_prev }
    })

@blog_bp.route('/search', methods=['GET'])
def search_posts():
    query = request.args.get('q', '', type=str)
    if not query:
        return jsonify([])
    
    posts = Post.query.filter(
        Post.title.ilike(f'%{query}%') | Post.excerpt.ilike(f'%{query}%')
    ).order_by(Post.date_posted.desc()).limit(20).all()
    
    return jsonify([p.to_dict() for p in posts])

@blog_bp.route('/posts/<string:slug>', methods=['GET'])
def get_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return jsonify(post.to_dict())

@blog_bp.route('/posts/<string:slug>/related', methods=['GET'])
def get_related_content(slug):
    current_post = Post.query.filter_by(slug=slug).first_or_404()
    prev_post = Post.query.filter(Post.date_posted < current_post.date_posted).order_by(Post.date_posted.desc()).first()
    next_post = Post.query.filter(Post.date_posted > current_post.date_posted).order_by(Post.date_posted.asc()).first()
    more_in_category = []
    if current_post.category:
        more_in_category = Post.query.filter(Post.category_id == current_post.category_id, Post.id != current_post.id).order_by(func.rand()).limit(2).all()
    in_this_series = []
    readlist_ids = [assoc.readlist_id for assoc in current_post.readlist_associations]
    if readlist_ids:
        all_related_posts = Post.query.join(PostReadlistOrder).filter(PostReadlistOrder.readlist_id.in_(readlist_ids), Post.id != current_post.id).distinct().all()
        random.shuffle(all_related_posts)
        in_this_series = all_related_posts[:2]

    return jsonify({
        'previousPost': prev_post.to_dict() if prev_post else None,
        'nextPost': next_post.to_dict() if next_post else None,
        'moreInCategory': [p.to_dict() for p in more_in_category],
        'inThisSeries': [p.to_dict() for p in in_this_series]
    })

@blog_bp.route('/posts/<string:slug>/view', methods=['POST'])
def increment_view_count(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    post.view_count += 1
    db.session.commit()
    return jsonify({'message': 'View count updated.'})

@blog_bp.route('/readlists/<string:slug>', methods=['GET'])
def get_readlist(slug):
    readlist = Readlist.query.filter_by(slug=slug).first_or_404()
    return jsonify(readlist.to_dict(include_posts=True))
    
@blog_bp.route('/categories', methods=['GET'])
def get_all_public_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify([c.to_dict() for c in categories])

@blog_bp.route('/categories/<string:slug>', methods=['GET'])
def get_category_page(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    posts = Post.query.filter_by(category_id=category.id).order_by(Post.date_posted.desc()).all()
    return jsonify({
        'category': category.to_dict(),
        'posts': [p.to_dict() for p in posts]
    })

# --- Admin Routes ---
@blog_bp.route('/upload-image', methods=['POST'])
@jwt_required()
def upload_blog_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{int(time.time())}_{filename}"
        
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        file_url = f"/static/uploads/{unique_filename}"
        
        return jsonify({'url': file_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/admin/posts', methods=['GET'])
@jwt_required()
def get_all_posts_admin():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return jsonify([p.to_dict(include_readlists=True) for p in posts])

@blog_bp.route('/admin/posts', methods=['POST'])
@jwt_required()
def create_post():
    data = request.get_json()
    new_post = Post(
        title=data['title'], slug=data['slug'], content=data['content'],
        excerpt=data.get('excerpt'), image_url=data.get('image_url'),
        is_featured=data.get('is_featured', False), category_id=data.get('category_id')
    )
    db.session.add(new_post)
    db.session.commit()
    if 'readlist_ids' in data:
        for rl_id in data['readlist_ids']:
            readlist = Readlist.query.get(rl_id)
            if readlist:
                assoc = PostReadlistOrder(post=new_post, readlist=readlist)
                db.session.add(assoc)
        db.session.commit()
    return jsonify(new_post.to_dict()), 201

@blog_bp.route('/admin/posts/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post_admin(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict(include_readlists=True))

@blog_bp.route('/admin/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    post.title = data.get('title', post.title); post.slug = data.get('slug', post.slug)
    post.content = data.get('content', post.content); post.excerpt = data.get('excerpt', post.excerpt)
    post.image_url = data.get('image_url', post.image_url); post.is_featured = data.get('is_featured', post.is_featured)
    post.category_id = data.get('category_id', post.category_id)
    
    if 'readlist_ids' in data:
        PostReadlistOrder.query.filter_by(post_id=post.id).delete()
        for rl_id in data['readlist_ids']:
            readlist = Readlist.query.get(rl_id)
            if readlist:
                assoc = PostReadlistOrder(post=post, readlist=readlist)
                db.session.add(assoc)

    db.session.commit()
    return jsonify(post.to_dict(include_readlists=True))

@blog_bp.route('/admin/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'})

@blog_bp.route('/admin/readlists', methods=['GET'])
@jwt_required()
def get_all_readlists_admin():
    readlists = Readlist.query.order_by(Readlist.order.asc()).all()
    return jsonify([rl.to_dict(include_posts=True) for rl in readlists])

@blog_bp.route('/admin/readlists/<int:readlist_id>', methods=['GET'])
@jwt_required()
def get_single_readlist_admin(readlist_id):
    readlist = Readlist.query.get_or_404(readlist_id)
    return jsonify(readlist.to_dict(include_posts=True))

@blog_bp.route('/admin/readlists', methods=['POST'])
@jwt_required()
def create_readlist():
    data = request.get_json()
    new_readlist = Readlist(
        name=data['name'], slug=data['slug'], description=data.get('description'), 
        order=data.get('order', 0), image_url=data.get('image_url')
    )
    db.session.add(new_readlist)
    db.session.commit()
    return jsonify(new_readlist.to_dict()), 201

@blog_bp.route('/admin/readlists/<int:readlist_id>', methods=['PUT'])
@jwt_required()
def update_readlist(readlist_id):
    readlist = Readlist.query.get_or_404(readlist_id)
    data = request.get_json()
    readlist.name = data.get('name', readlist.name); readlist.slug = data.get('slug', readlist.slug)
    readlist.description = data.get('description', readlist.description); readlist.order = data.get('order', readlist.order)
    readlist.image_url = data.get('image_url', readlist.image_url)
    
    if 'posts' in data:
        PostReadlistOrder.query.filter_by(readlist_id=readlist.id).delete()
        for i, post_data in enumerate(data['posts']):
            post = Post.query.get(post_data['id'])
            if post:
                assoc = PostReadlistOrder(post=post, readlist=readlist, post_order=i)
                db.session.add(assoc)

    db.session.commit()
    return jsonify(readlist.to_dict(include_posts=True))

@blog_bp.route('/admin/readlists/<int:readlist_id>', methods=['DELETE'])
@jwt_required()
def delete_readlist(readlist_id):
    readlist = Readlist.query.get_or_404(readlist_id)
    db.session.delete(readlist)
    db.session.commit()
    return jsonify({'message': 'Readlist deleted.'})

@blog_bp.route('/admin/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = Category.query.order_by(Category.name.asc()).all()
    return jsonify([c.to_dict() for c in categories])

@blog_bp.route('/admin/categories', methods=['POST'])
@jwt_required()
def create_category():
    data = request.get_json()
    new_category = Category(name=data['name'], slug=data['slug'], color=data['color'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

@blog_bp.route('/admin/categories/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def delete_category(cat_id):
    category = Category.query.get_or_404(cat_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted.'})