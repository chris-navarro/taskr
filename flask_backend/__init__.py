from flask import Flask, request
from flask_login import current_user
from config import Config
from .database import mongo
from .extensions import bcrypt, login_manager
from .models.user import User

def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    mongo.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @app.after_request
    def record_user_activity(response):
        if current_user.is_authenticated and not request.path.startswith("/static"):
            try:
                from .models.audit_log import AuditLog
                AuditLog.record_activity(
                    current_user.id,
                    "view" if request.method == "GET" else "action",
                    request.endpoint,
                    request.method,
                    response.status_code,
                    request.path,
                )
            except Exception:
                pass
        return response

    @login_manager.user_loader
    def load_user(user_id):
        return User.from_id(user_id, mongo.db.users)

    # Blueprints registration
    from .routes                               import routes
    from .tasks                                import tasks
    from .journal                              import journal
    from .task_updates                          import task_updates_bp

    app.register_blueprint(routes)
    app.register_blueprint(tasks)
    app.register_blueprint(journal)
    app.register_blueprint(task_updates_bp)

    return app