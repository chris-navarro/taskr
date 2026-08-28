from functools import wraps
from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
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
    return render_template(
        "admin.html",
        categories=WorkspaceSettings.categories(),
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