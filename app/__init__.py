from flask import Flask

def create_app():
    app = Flask(__name__, 
                template_folder="templates",
                static_folder="static")
    
    app.secret_key = "fh-rflp-screening-2026"
    
    # Register routes
    from app.routes import main
    app.register_blueprint(main)
    
    return app