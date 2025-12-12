from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config import Config
import cloudinary

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)
    db.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    cloudinary.config(
        cloud_name = app.config['CLOUDINARY_CLOUD_NAME'],
        api_key = app.config['CLOUDINARY_API_KEY'],
        api_secret = app.config['CLOUDINARY_API_SECRET']
    )

    from app.models import project, product, admin, about, blog, order

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return admin.Admin.query.get(identity)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Token is invalid.", "error": str(error)}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Request does not contain an access token."}), 401

    from app.routes.portfolio_routes import portfolio_bp
    from app.routes.blog_routes import blog_bp
    from app.routes.marketplace_routes import marketplace_bp
    from app.routes.contact_routes import contact_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.about_routes import about_bp

    app.register_blueprint(portfolio_bp, url_prefix='/api/portfolio')
    app.register_blueprint(blog_bp, url_prefix='/api/blog')
    app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace')
    app.register_blueprint(contact_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(about_bp, url_prefix='/api/about')

    return app