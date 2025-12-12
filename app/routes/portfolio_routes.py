from flask import Blueprint, jsonify, request
from app.models.project import Project
from app import db
from flask_jwt_extended import jwt_required
import cloudinary
import cloudinary.uploader

portfolio_bp = Blueprint('portfolio_bp', __name__)

@portfolio_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        upload_result = cloudinary.uploader.upload(file, resource_type="auto")
        return jsonify({'secure_url': upload_result['secure_url']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@portfolio_bp.route('/projects', methods=['GET'])
def get_projects():
    projects = Project.query.order_by(Project.order.asc()).all()
    return jsonify([project.to_dict() for project in projects])

@portfolio_bp.route('/projects', methods=['POST'])
@jwt_required()
def add_project():
    data = request.get_json()
    new_project = Project(
        title=data['title'],
        description=data['description'],
        tech_stack=data.get('tech_stack'),
        tools=data.get('tools'),
        live_url=data.get('live_url'),
        github_url=data.get('github_url'),
        image_url=data.get('image_url'),
        video_url=data.get('video_url'),
        duration=data.get('duration'),
        cost=data.get('cost'),
        collaborators=data.get('collaborators'),
        order=data.get('order', 0)
    )
    db.session.add(new_project)
    db.session.commit()
    return jsonify(new_project.to_dict()), 201

@portfolio_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    project.title = data.get('title', project.title)
    project.description = data.get('description', project.description)
    project.tech_stack = data.get('tech_stack', project.tech_stack)
    project.tools = data.get('tools', project.tools)
    project.live_url = data.get('live_url', project.live_url)
    project.github_url = data.get('github_url', project.github_url)
    project.image_url = data.get('image_url', project.image_url)
    project.video_url = data.get('video_url', project.video_url)
    project.duration = data.get('duration', project.duration)
    project.cost = data.get('cost', project.cost)
    project.collaborators = data.get('collaborators', project.collaborators)
    project.order = data.get('order', project.order)
    db.session.commit()
    return jsonify(project.to_dict())

@portfolio_bp.route('/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted successfully'})