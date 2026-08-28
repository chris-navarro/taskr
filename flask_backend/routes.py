import os
import sqlite3
import sys
import threading
import time
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import quote, urlsplit, urlunsplit

from dotenv import set_key
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from .database import mongo
from .extensions import bcrypt
from .models.user import User
from .models.task import Task
from .models.workspace_settings import WorkspaceSettings
from .models.audit_log import AuditLog


def task_lifecycle_badge(task):
    status = (task.get("status") or "Planning").lower()
    if status in {"completed", "cancelled", "canceled"}:
        return status.title().replace("Canceled", "Cancelled")
    if (task.get("updated_at") and task.get("created_at") and
            task["updated_at"] - task["created_at"] > timedelta(seconds=1)):
        return "Updated"
    return "New"


def task_timeline_badge(task):
    if (task.get("status") or "").lower() in {"completed", "cancelled", "canceled"}:
        return "Within timeline", "success"
    now = datetime.utcnow()
    due_date = task.get("due_date")
    start_date = task.get("start_date")
    if due_date and now > due_date:
        return "Beyond timeline", "danger"
    if not start_date or not due_date or due_date <= start_date:
        return "Timeline unavailable", "secondary"
    elapsed = (now - start_date).total_seconds()
    duration = (due_date - start_date).total_seconds()
    elapsed_ratio = elapsed / duration
    expected_progress = max(0, min(100, elapsed_ratio * 100))
    current_progress = task.get("progress", 0) or 0
    if elapsed_ratio >= 0.1 and current_progress + 25 < expected_progress:
        return "Timeline at risk", "warning"
    return "Within timeline", "success"
from flask_login import current_user, login_required, login_user, logout_user

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("routes.dashboard"))
    return render_template("index.html")

def role_required(*roles):
    allowed_roles = {role.title() for role in roles}
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role(*allowed_roles):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@routes.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(
            url_for("routes.dashboard")
        )
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = "remember" in request.form
        document = mongo.db.users.find_one({
            "username": username
        })
        stored_password = document.get("password") if document else None
        if stored_password and bcrypt.check_password_hash(stored_password, password):
            login_user(
                User(document),
                remember=remember
            )
            flash(
                f"Welcome back, {document['fullname']}!",
                "success"
            )
            return redirect(
                url_for("routes.dashboard")
            )
        flash(

            "Invalid username or password.",
            "danger"
        )

    return render_template("login.html")

@routes.route("/logout")
@login_required
def logout():
    logout_user()
    flash(

        "You have been logged out.",
        "info"
    )
    return redirect(url_for("routes.index"))


@routes.route("/dashboard")
@login_required
def dashboard():
    tasks = Task.all(owner_id=current_user.id)
    counts = Task.dashboard_counts(current_user.id)
    counts["average_progress"] = round(
        sum(task.get("progress", 0) for task in tasks) / len(tasks)
    ) if tasks else 0
    milestones = [task for task in tasks if task.get("milestone")][:6]
    for task in milestones:
        task["lifecycle_badge"] = task_lifecycle_badge(task)
        task["timeline_badge"], task["timeline_color"] = task_timeline_badge(task)
    return render_template(
        "dashboard.html",
        counts=counts,
        milestones=milestones,
    )


@routes.route("/admin")
@role_required("Admin", "Administrator")
def admin():
    settings = storage_settings()
    return render_template(
        "admin.html",
        categories=WorkspaceSettings.categories(),
        storage=settings,
        storage_health=storage_health(settings["backend"], settings["mongo_uri"], settings["sqlite_path"]),
    )


@routes.route("/admin/categories", methods=["POST"])
@role_required("Admin", "Administrator")
def add_category():
    category = request.form.get("category", "")
    if not category.strip():
        flash("Category name is required.", "danger")
    else:
        WorkspaceSettings.add_category(category)
        flash("Category added.", "success")
    return redirect(url_for("routes.admin"))


@routes.route("/admin/categories/<path:category>/delete", methods=["POST"])
@role_required("Admin", "Administrator")
def delete_category(category):
    if WorkspaceSettings.remove_category(category):
        flash("Category removed.", "success")
    else:
        flash("Default categories cannot be removed.", "warning")
    return redirect(url_for("routes.admin"))


def storage_settings():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/taskr")
    parsed = urlsplit(mongo_uri)
    if parsed.username or parsed.password:
        host = parsed.hostname or ""
        if parsed.port:
            host += f":{parsed.port}"
        mongo_uri = urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))
    return {
        "backend": os.getenv("DB_BACKEND", "mongo").lower(),
        "sqlite_path": os.getenv("SQLITE_PATH", "taskr.sqlite3"),
        "mongo_uri": mongo_uri,
    }


def mongo_uri_with_credentials(uri, username, password):
    if not username and not password:
        return uri.strip()
    parsed = urlsplit(uri.strip())
    if parsed.scheme not in {"mongodb", "mongodb+srv"} or not parsed.hostname:
        raise ValueError("Enter a valid MongoDB URI before adding credentials.")
    host = parsed.hostname
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    netloc = f"{quote(username, safe='')}:{quote(password, safe='')}@{host}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def validate_storage(backend, mongo_uri, sqlite_path):
    if backend == "sqlite":
        connection = sqlite3.connect(sqlite_path)
        try:
            connection.execute("SELECT 1")
        finally:
            connection.close()
        return
    if backend != "mongo":
        raise ValueError("Choose MongoDB or SQLite3.")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    try:
        client.admin.command("ping")
    finally:
        client.close()


def restart_application():
    time.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)


def schedule_restart():
    thread = threading.Thread(target=restart_application, daemon=True)
    thread.start()


def storage_health(backend, mongo_uri, sqlite_path):
    try:
        validate_storage(backend, mongo_uri, sqlite_path)
        return {"backend": backend, "installed": True, "reachable": True, "message": "Installed and reachable."}
    except ImportError:
        return {"backend": backend, "installed": False, "reachable": False, "message": "The required database driver is not installed."}
    except Exception:
        return {"backend": backend, "installed": True, "reachable": False, "message": "Installed, but not reachable with these settings."}


@routes.route("/admin/storage", methods=["POST"])
@role_required("Admin", "Administrator")
def update_storage():
    backend = request.form.get("backend", "mongo").lower()
    sqlite_path = request.form.get("sqlite_path", "taskr.sqlite3").strip() or "taskr.sqlite3"
    mongo_uri = request.form.get("mongo_uri", "").strip()
    username = request.form.get("mongo_username", "").strip()
    password = request.form.get("mongo_password", "")
    env_path = os.path.join(os.getcwd(), ".env")
    try:
        if backend == "mongo":
            mongo_uri = mongo_uri_with_credentials(mongo_uri, username, password)
        validate_storage(backend, mongo_uri, sqlite_path)
        set_key(env_path, "DB_BACKEND", backend)
        set_key(env_path, "SQLITE_PATH", sqlite_path)
        if backend == "mongo":
            set_key(env_path, "MONGO_URI", mongo_uri)
        os.chmod(env_path, 0o600)
    except Exception:
        flash("Storage settings were not saved. Check the backend availability and connection details.", "danger")
        return redirect(url_for("routes.admin"))
    flash("Storage settings saved. Taskr is restarting to apply the new backend.", "success")
    schedule_restart()
    return redirect(url_for("routes.admin"))


@routes.route("/admin/storage/check", methods=["POST"])
@role_required("Admin", "Administrator")
def check_storage():
    backend = request.form.get("backend", "mongo").lower()
    sqlite_path = request.form.get("sqlite_path", "taskr.sqlite3").strip() or "taskr.sqlite3"
    mongo_uri = request.form.get("mongo_uri", "").strip()
    try:
        if backend == "mongo":
            mongo_uri = mongo_uri_with_credentials(
                mongo_uri,
                request.form.get("mongo_username", "").strip(),
                request.form.get("mongo_password", ""),
            )
        result = storage_health(backend, mongo_uri, sqlite_path)
    except ValueError as error:
        result = {"backend": backend, "installed": True, "reachable": False, "message": str(error)}
    return jsonify(result), 200 if result["reachable"] else 503


@routes.route("/admin/audit")
@role_required("Admin", "Administrator")
def audit():
    return render_template("audit.html", audit_logs=AuditLog.recent())

# Testing the mongodb connection
@routes.route("/test-db")
def test_db():

    mongo.db.test.insert_one({

        "message": "MongoDB Connected"

    })
    return "Test Document Inserted Successfully!"