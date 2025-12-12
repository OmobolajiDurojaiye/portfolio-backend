from flask import Blueprint, jsonify, request
from app.models.about import About, Skill, Tool, WorkExperience
from app import db
from flask_jwt_extended import jwt_required

about_bp = Blueprint('about_bp', __name__)

# --- Public Route ---
@about_bp.route('/', methods=['GET'])
def get_about_data():
    about_content = About.query.first()
    if not about_content:
        # Create default content if none exists
        about_content = About(bio="Welcome to my page. Edit this bio in the admin panel.")
        db.session.add(about_content)
        db.session.commit()

    skills = Skill.query.all()
    tools = Tool.query.all()
    work_experiences = WorkExperience.query.order_by(WorkExperience.order.asc()).all()

    return jsonify({
        'bio': about_content.bio,
        'spotify_url': about_content.spotify_url,
        'skills': [skill.to_dict() for skill in skills],
        'tools': [tool.to_dict() for tool in tools],
        'work_experiences': [exp.to_dict() for exp in work_experiences]
    })

# --- Admin Routes ---
@about_bp.route('/', methods=['POST'])
@jwt_required()
def update_about_main():
    data = request.get_json()
    about_content = About.query.first()
    if not about_content:
        about_content = About()
        db.session.add(about_content)
    
    about_content.bio = data.get('bio', about_content.bio)
    about_content.spotify_url = data.get('spotify_url', about_content.spotify_url)
    db.session.commit()
    return jsonify({'message': 'About content updated successfully.'})

# --- Skills Management ---
@about_bp.route('/skills', methods=['POST'])
@jwt_required()
def add_skill():
    data = request.get_json()
    new_skill = Skill(name=data['name'], icon_name=data['icon_name'])
    db.session.add(new_skill)
    db.session.commit()
    return jsonify(new_skill.to_dict()), 201

@about_bp.route('/skills/<int:skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'message': 'Skill deleted.'})

# --- Tools Management ---
@about_bp.route('/tools', methods=['POST'])
@jwt_required()
def add_tool():
    data = request.get_json()
    new_tool = Tool(name=data['name'], icon_name=data['icon_name'])
    db.session.add(new_tool)
    db.session.commit()
    return jsonify(new_tool.to_dict()), 201

@about_bp.route('/tools/<int:tool_id>', methods=['DELETE'])
@jwt_required()
def delete_tool(tool_id):
    tool = Tool.query.get_or_404(tool_id)
    db.session.delete(tool)
    db.session.commit()
    return jsonify({'message': 'Tool deleted.'})

# --- Work Experience Management ---
@about_bp.route('/work-experiences', methods=['POST'])
@jwt_required()
def add_work_experience():
    data = request.get_json()
    new_exp = WorkExperience(
        role=data['role'], 
        company=data['company'], 
        duration=data['duration'],
        description=data.get('description'),
        order=data.get('order', 0)
    )
    db.session.add(new_exp)
    db.session.commit()
    return jsonify(new_exp.to_dict()), 201

@about_bp.route('/work-experiences/<int:exp_id>', methods=['PUT'])
@jwt_required()
def update_work_experience(exp_id):
    exp = WorkExperience.query.get_or_404(exp_id)
    data = request.get_json()
    exp.role = data.get('role', exp.role)
    exp.company = data.get('company', exp.company)
    exp.duration = data.get('duration', exp.duration)
    exp.description = data.get('description', exp.description)
    exp.order = data.get('order', exp.order)
    db.session.commit()
    return jsonify(exp.to_dict())

@about_bp.route('/work-experiences/<int:exp_id>', methods=['DELETE'])
@jwt_required()
def delete_work_experience(exp_id):
    exp = WorkExperience.query.get_or_404(exp_id)
    db.session.delete(exp)
    db.session.commit()
    return jsonify({'message': 'Work experience deleted.'})