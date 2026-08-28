from datetime import datetime, timedelta

from bson import ObjectId

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    jsonify
)

from flask_login import (
    login_required,
    current_user
)

from .models.task import Task
from .models.task_update import TaskUpdate
from .models.workspace_settings import WorkspaceSettings


def parse_recorded_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed


def lifecycle_badge(task):
    status = (task.get("status") or "Planning").lower()
    if status in {"completed", "cancelled", "canceled"}:
        return status.title().replace("Canceled", "Cancelled")
    if (task.get("updated_at") and task.get("created_at") and
            task["updated_at"] - task["created_at"] > timedelta(seconds=1)):
        return "Updated"
    return "New"

tasks = Blueprint(
    "tasks",
    __name__,
    url_prefix="/tasks"
)

PER_PAGE = 10


###########################################################################
# TASK LIST
###########################################################################

@tasks.route("/")
@login_required
def index():

    keyword = request.args.get("q", "").strip()

    page = request.args.get("page", 1, type=int)

    tasks_data, total = Task.paginate(
        keyword=keyword,
        page=page,
        per_page=PER_PAGE,
        owner_id=current_user.id
    )
    for task in tasks_data:
        task["lifecycle_badge"] = lifecycle_badge(task)

    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    return render_template(
        "tasks/index.html",
        tasks=tasks_data,
        keyword=keyword,
        page=page,
        total_pages=total_pages,
        categories=WorkspaceSettings.categories(),
        counts=Task.dashboard_counts(current_user.id),
    )


###########################################################################
# CREATE TASK
###########################################################################

@tasks.route("/create", methods=["POST"])
@login_required
def create():

    subject = request.form.get("subject", "").strip()

    project_id = request.form.get("project_id", "").strip()

    description = request.form.get("description", "").strip()

    priority = request.form.get("priority", "Medium")

    status = request.form.get("status", "Planning")
    tags = [tag.strip() for tag in request.form.get("tags", "").split(",") if tag.strip()]
    parent_task = request.form.get("parent_task", "").strip()

    start_date = request.form.get("start_date")

    due_date = request.form.get("due_date")

    try:
        estimated_hours = float(request.form.get("estimated_hours", 0))
    except (TypeError, ValueError):
        estimated_hours = -1

    errors = []

    if len(subject) == 0:
        errors.append("Subject is required.")

    if len(subject) > 150:
        errors.append("Subject cannot exceed 150 characters.")

    if start_date == "":
        errors.append("Start date is required.")

    if due_date == "":
        errors.append("Due date is required.")

    if estimated_hours < 0:
        errors.append("Estimated hours must be zero or greater.")

    try:
        parsed_start_date = datetime.fromisoformat(start_date)
        parsed_due_date = datetime.fromisoformat(due_date)
        if parsed_due_date < parsed_start_date:
            errors.append("Due date must be on or after the start date.")
    except (TypeError, ValueError):
        errors.append("Enter valid start and due dates.")

    if errors:

        for error in errors:
            flash(error, "danger")

        if request.headers.get("Accept") == "application/json":
            return jsonify(error=" ".join(errors)), 400
        return redirect(url_for("tasks.index"))

    document = {

        "subject": subject,

        "project_id": project_id,

        "description": description,
        "category": request.form.get("category", "Development"),
        "milestone": request.form.get("milestone", "").strip(),

        "priority": priority,

        "status": status,

        "progress": 0,

        "owner_id": ObjectId(current_user.id),

        "created_by": ObjectId(current_user.id),

        "start_date": parsed_start_date,

        "due_date": parsed_due_date,

        "completed_date": None,

        "estimated_hours": estimated_hours,

        "actual_hours": 0,

        "dependencies": [],

        "tags": tags,
        "parent_task": ObjectId(parent_task) if ObjectId.is_valid(parent_task) else None,
        "completion_criteria": request.form.get("completion_criteria", "").strip(),
        "remarks": request.form.get("remarks", ""),

        "created_at": datetime.utcnow(),

        "updated_at": datetime.utcnow(),

        "deleted": False

    }

    result = Task.create(document)

    flash(
        "Task successfully created.",
        "success"
    )

    if request.headers.get("Accept") == "application/json":
        return jsonify(task={
            "_id": str(result.inserted_id),
            "subject": subject,
            "project_id": project_id,
            "status": status,
            "priority": priority,
            "progress": 0,
            "due_date": parsed_due_date.strftime("%b %d, %Y")
        }), 201

    return redirect(url_for("tasks.index"))


###########################################################################
# TASK DETAILS
###########################################################################

@tasks.route("/<task_id>")
@login_required
def detail(task_id):

    task = Task.get(task_id)

    if task is None:

        abort(404)

    updates = TaskUpdate.for_task(task_id)
    task["lifecycle_badge"] = lifecycle_badge(task)

    return render_template(

        "tasks/detail.html",

        task=task,
        updates=updates

    )

###########################################################################
# EDIT TASK
###########################################################################

@tasks.route("/edit/<task_id>", methods=["POST"])
@login_required
def edit(task_id):

    task = Task.get(task_id)

    if task is None:

        abort(404)

    update = {

        "subject": request.form.get("subject", "").strip(),

        "project_id": request.form.get("project_id", "").strip(),

        "description": request.form.get("description", "").strip(),

        "category": request.form.get("category", "Development").strip(),

        "milestone": request.form.get("milestone", "").strip(),

        "priority": request.form.get("priority"),

        "status": request.form.get("status"),

        "updated_at": datetime.utcnow()

    }

    Task.update(

        task_id,

        update

    )

    flash(

        "Task updated successfully.",

        "success"

    )

    return redirect(

        url_for(

            "tasks.detail",

            task_id=task_id

        )

    )


@tasks.route("/<task_id>/updates", methods=["POST"])
@login_required
def add_update(task_id):
    task = Task.get(task_id)
    if task is None:
        abort(404)

    try:
        worked_at = request.form.get("worked_at") or request.form.get("date_worked", "")
        date_worked = parse_recorded_datetime(worked_at)
        if date_worked is None:
            raise ValueError("A work date is required.")
        updated_start_date = parse_recorded_datetime(request.form.get("update_start_date"))
        updated_due_date = parse_recorded_datetime(request.form.get("update_due_date"))
        if updated_start_date is None or updated_due_date is None:
            raise ValueError("Start and due dates are required.")
        if updated_due_date < updated_start_date:
            raise ValueError("Due date must be on or after the start date.")
        hours_worked = float(request.form.get("hours_worked", "0"))
        estimated_hours = float(request.form.get("estimated_hours", task.get("estimated_hours", 0)))
        progress = int(request.form.get("progress", task.get("progress", 0)))
    except (TypeError, ValueError):
        flash("Enter a valid work date, hours, and progress.", "danger")
        return redirect(url_for("tasks.detail", task_id=task_id))

    status = request.form.get("status") or "In Progress"
    if hours_worked < 0 or estimated_hours < 0 or not 0 <= progress <= 100:
        flash("Hours must be zero or greater and progress must be between 0 and 100.", "danger")
        return redirect(url_for("tasks.detail", task_id=task_id))

    if progress == 100:
        status = "Completed"

    date_change_reason = request.form.get("date_change_reason", "").strip()
    dates_changed = (
        updated_start_date != task.get("start_date") or
        updated_due_date != task.get("due_date")
    )
    if dates_changed and not date_change_reason:
        flash("Provide a justification when changing the task dates.", "danger")
        return redirect(url_for("tasks.detail", task_id=task_id))

    remarks = request.form.get("remarks", "").strip()
    if date_change_reason:
        remarks = f"Date change justification: {date_change_reason}\n{remarks}".strip()

    TaskUpdate.create(
        task_id=task_id,
        user_id=current_user.id,
        progress=progress,
        hours_worked=hours_worked,
        status=status,
        accomplishment=request.form.get("accomplishments", ""),
        blockers=request.form.get("challenges", ""),
        next_steps=request.form.get("next_steps", ""),
        remarks=remarks,
        worked_at=date_worked
    )
    Task.update(task_id, {
        "start_date": updated_start_date,
        "due_date": updated_due_date,
        "estimated_hours": estimated_hours,
    })
    Task.update_progress(task_id, progress, status=status, hours_worked=hours_worked)
    flash("Work update recorded.", "success")
    return redirect(url_for("tasks.detail", task_id=task_id))


###########################################################################
# DELETE TASK
###########################################################################

@tasks.route("/delete/<task_id>", methods=["POST"])
@login_required
def delete(task_id):

    task = Task.get(task_id)

    if task is None:

        abort(404)

    Task.delete(task_id)

    flash(

        "Task deleted.",

        "warning"

    )

    return redirect(

        url_for("tasks.index")

    )