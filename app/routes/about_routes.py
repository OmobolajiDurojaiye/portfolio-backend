from flask import Blueprint, jsonify, request
from app.models.about import About, Skill, Tool, WorkExperience
from app import db
from flask_jwt_extended import jwt_required
import requests
import base64
import os

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

# --- Spotify Integration Route ---
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")

def get_spotify_access_token():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET or not SPOTIFY_REFRESH_TOKEN:
        return None
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN
    }
    try:
        res = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data, timeout=5)
        if res.status_code == 200:
            return res.json().get("access_token")
    except Exception as e:
        print("Spotify token error:", e)
    return None

@about_bp.route('/spotify', methods=['GET'])
def get_spotify_now_playing():
    access_token = get_spotify_access_token()
    
    # Default/Offline Fallback Response (using user's actual profile URL)
    default_track = {
        "is_playing": False,
        "title": "Last Last",
        "artist": "Burna Boy",
        "album_art": "https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=300&auto=format&fit=crop",
        "progress_ms": 180000,
        "duration_ms": 230000,
        "track_url": "https://open.spotify.com/user/31uyiyix7zv5vnia63hcvdt4xzry?si=67e9059882504770"
    }

    if not access_token:
        return jsonify(default_track)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        # 1. Query currently playing
        res = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers, timeout=5)
        if res.status_code == 200 and res.content:
            data = res.json()
            item = data.get("item")
            if item:
                album = item.get("album", {})
                images = album.get("images", [])
                album_art = images[0].get("url") if images else default_track["album_art"]
                return jsonify({
                    "is_playing": data.get("is_playing", False),
                    "title": item.get("name"),
                    "artist": ", ".join([artist.get("name") for artist in item.get("artists", [])]),
                    "album_art": album_art,
                    "progress_ms": data.get("progress_ms", 0),
                    "duration_ms": item.get("duration_ms", 0),
                    "track_url": item.get("external_urls", {}).get("spotify", default_track["track_url"])
                })
        
        # 2. If nothing playing, query recently played
        res = requests.get("https://api.spotify.com/v1/me/player/recently-played?limit=1", headers=headers, timeout=5)
        if res.status_code == 200 and res.content:
            data = res.json()
            items = data.get("items", [])
            if items:
                track = items[0].get("track")
                if track:
                    album = track.get("album", {})
                    images = album.get("images", [])
                    album_art = images[0].get("url") if images else default_track["album_art"]
                    return jsonify({
                        "is_playing": False,
                        "title": track.get("name"),
                        "artist": ", ".join([artist.get("name") for artist in track.get("artists", [])]),
                        "album_art": album_art,
                        "progress_ms": 0,
                        "duration_ms": track.get("duration_ms", 0),
                        "track_url": track.get("external_urls", {}).get("spotify", default_track["track_url"])
                    })
    except Exception as e:
        print("Spotify now playing error:", e)

    return jsonify(default_track)