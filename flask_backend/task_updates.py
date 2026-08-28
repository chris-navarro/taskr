"""
Task Update Routes

Handles creation, editing, and deletion of historical
task progress/activity records.
"""

from datetime import datetime

from bson import ObjectId
from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for
)
from flask_login import current_user, login_required

from .models.task import Task
from .models.task_update import TaskUpdate
from .models.audit_log import AuditLog


task_updates_bp = Blueprint(
    "task_updates",
    __name__,
    url_prefix="/tasks"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_progress(value):
    """
    Convert progress into an integer between 0 and 100.
    """

    try:

        progress = int(value)

    except (TypeError, ValueError):

        raise ValueError(
            "Progress must be a whole number."
        )

    if progress < 0 or progress > 100:

        raise ValueError(
            "Progress must be between 0 and 100."
        )

    return progress


def parse_hours(value):
    """
    Convert hours worked into a non-negative float.
    """

    try:

        hours = float(value)

    except (TypeError, ValueError):

        raise ValueError(
            "Hours worked must be a valid number."
        )

    if hours < 0:

        raise ValueError(
            "Hours worked cannot be negative."
        )

    return hours


def parse_worked_at(value):
    """
    Convert HTML datetime-local value into a Python datetime.
    """

    if not value:

        return datetime.utcnow()

    try:

        return datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M"
        )

    except ValueError:

        raise ValueError(
            "Invalid work date and time."
        )


def get_task_for_user(task_id):
    """
    Retrieve a task and verify that it belongs to the
    current authenticated user.

    This prevents a user from modifying another user's task
    simply by changing the task ID in the URL.
    """

    try:

        task = Task.get(task_id)

    except Exception:

        return None

    if not task:

        return None

    owner_id = task.get("owner_id")

    if not owner_id:

        return None

    if str(owner_id) != str(current_user.id):

        return None

    return task


# ============================================================
# CREATE TASK UPDATE
# ============================================================

@task_updates_bp.route(
    "/<task_id>/updates/create",
    methods=["POST"]
)
@login_required
def create(task_id):
    """
    Create a new historical progress update.
    """

    task = get_task_for_user(task_id)

    if not task:

        flash(
            "Task not found or you do not have permission to update it.",
            "danger"
        )

        return redirect(
            url_for("tasks.index")
        )

    try:

        progress = parse_progress(

            request.form.get(
                "progress",
                0
            )

        )

        hours_worked = parse_hours(

            request.form.get(
                "hours_worked",
                0
            )

        )

        worked_at = parse_worked_at(

            request.form.get(
                "worked_at"
            )

        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    status = request.form.get(
        "status",
        "In Progress"
    ).strip()

    accomplishment = request.form.get(
        "accomplishment",
        ""
    ).strip()

    blockers = request.form.get(
        "blockers",
        ""
    ).strip()

    next_steps = request.form.get(
        "next_steps",
        ""
    ).strip()

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    errors = []

    if not accomplishment and progress > 0:

        errors.append(
            "Please describe what you accomplished."
        )

    if len(accomplishment) > 5000:

        errors.append(
            "Accomplishment is too long."
        )

    if len(blockers) > 5000:

        errors.append(
            "Blockers description is too long."
        )

    if len(next_steps) > 5000:

        errors.append(
            "Next steps description is too long."
        )

    if len(remarks) > 5000:

        errors.append(
            "Remarks are too long."
        )

    allowed_statuses = {

        "Planning",

        "In Progress",

        "On Hold",

        "Completed",

        "Cancelled",

        "Blocked"

    }

    if status not in allowed_statuses:

        errors.append(
            "Invalid task status."
        )

    if errors:

        for error in errors:

            flash(
                error,
                "danger"
            )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    # --------------------------------------------------------
    # Automatically determine completed status
    # --------------------------------------------------------

    if progress >= 100:

        progress = 100

        status = "Completed"

    elif progress > 0 and status == "Planning":

        status = "In Progress"

    # --------------------------------------------------------
    # Create historical update
    # --------------------------------------------------------

    try:

        result = TaskUpdate.create(

            task_id=task_id,

            user_id=current_user.id,

            progress=progress,

            hours_worked=hours_worked,

            status=status,

            accomplishment=accomplishment,

            blockers=blockers,

            next_steps=next_steps,

            remarks=remarks,

            worked_at=worked_at

        )

        # ----------------------------------------------------
        # Update current task state
        # ----------------------------------------------------

        Task.update(

            task_id,

            {

                "progress": progress,

                "status": status,

                "actual_hours":
                    TaskUpdate.total_hours(
                        task_id
                    )

            }

        )

    except Exception:

        flash(

            "Unable to save the task update.",

            "danger"

        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    flash(

        "Task progress update recorded successfully.",

        "success"

    )

    return redirect(

        url_for(
            "tasks.detail",
            task_id=task_id
        )

    )


# ============================================================
# EDIT TASK UPDATE
# ============================================================

@task_updates_bp.route(
    "/<task_id>/updates/<update_id>/edit",
    methods=["POST"]
)
@login_required
def edit(task_id, update_id):
    """
    Edit an existing historical update.
    """

    task = get_task_for_user(task_id)

    if not task:

        flash(
            "Task not found.",
            "danger"
        )

        return redirect(
            url_for("tasks.index")
        )

    update = TaskUpdate.get(update_id)

    if not update:

        flash(
            "Task update not found.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    # --------------------------------------------------------
    # Verify update belongs to task
    # --------------------------------------------------------

    if str(update.get("task_id")) != str(task["_id"]):

        flash(
            "Invalid task update.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    # --------------------------------------------------------
    # Verify user owns update
    # --------------------------------------------------------

    if str(update.get("user_id")) != str(
        current_user.id
    ):

        flash(
            "You do not have permission to edit this update.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    try:

        progress = parse_progress(

            request.form.get(
                "progress"
            )

        )

        hours_worked = parse_hours(

            request.form.get(
                "hours_worked"
            )

        )

        worked_at = parse_worked_at(

            request.form.get(
                "worked_at"
            )

        )

    except ValueError as error:

        flash(
            str(error),
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    status = request.form.get(
        "status",
        "In Progress"
    ).strip()

    accomplishment = request.form.get(
        "accomplishment",
        ""
    ).strip()

    blockers = request.form.get(
        "blockers",
        ""
    ).strip()

    next_steps = request.form.get(
        "next_steps",
        ""
    ).strip()

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()

    allowed_statuses = {

        "Planning",

        "In Progress",

        "On Hold",

        "Completed",

        "Cancelled",

        "Blocked"

    }

    if status not in allowed_statuses:

        flash(
            "Invalid task status.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    if progress >= 100:

        progress = 100

        status = "Completed"

    elif progress > 0 and status == "Planning":

        status = "In Progress"

    values = {

        "progress": progress,

        "hours_worked": hours_worked,

        "status": status,

        "accomplishment": accomplishment,

        "blockers": blockers,

        "next_steps": next_steps,

        "remarks": remarks,

        "worked_at": worked_at

    }

    AuditLog.record("edited", task_id, update_id, current_user.id, update.copy())

    result = TaskUpdate.update(

        update_id,

        values

    )

    if not result or result.matched_count == 0:

        flash(

            "Unable to update the activity record.",

            "danger"

        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    # --------------------------------------------------------
    # Recalculate current task values
    # --------------------------------------------------------

    latest = TaskUpdate.latest(task_id)

    total_hours = TaskUpdate.total_hours(
        task_id
    )

    if latest:

        Task.update(

            task_id,

            {

                "progress":
                    latest.get(
                        "progress",
                        0
                    ),

                "status":
                    latest.get(
                        "status",
                        "Planning"
                    ),

                "actual_hours":
                    total_hours

            }

        )

    flash(

        "Task update successfully modified.",

        "success"

    )

    return redirect(

        url_for(
            "tasks.detail",
            task_id=task_id
        )

    )


# ============================================================
# DELETE TASK UPDATE
# ============================================================

@task_updates_bp.route(
    "/<task_id>/updates/<update_id>/delete",
    methods=["POST"]
)
@login_required
def delete(task_id, update_id):
    """
    Delete a historical task update.
    """

    task = get_task_for_user(task_id)

    if not task:

        flash(
            "Task not found.",
            "danger"
        )

        return redirect(
            url_for("tasks.index")
        )

    update = TaskUpdate.get(update_id)

    if not update:

        flash(
            "Task update not found.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    if str(update.get("task_id")) != str(
        task["_id"]
    ):

        flash(
            "Invalid task update.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    if str(update.get("user_id")) != str(
        current_user.id
    ):

        flash(
            "You do not have permission to delete this update.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    AuditLog.record("deleted", task_id, update_id, current_user.id, update.copy())
    result = TaskUpdate.delete(
        update_id
    )

    if not result or result.deleted_count == 0:

        flash(
            "Unable to delete task update.",
            "danger"
        )

        return redirect(

            url_for(
                "tasks.detail",
                task_id=task_id
            )

        )

    # --------------------------------------------------------
    # Recalculate task state after deletion
    # --------------------------------------------------------

    latest = TaskUpdate.latest(
        task_id
    )

    total_hours = TaskUpdate.total_hours(
        task_id
    )

    if latest:

        Task.update(

            task_id,

            {

                "progress":
                    latest.get(
                        "progress",
                        0
                    ),

                "status":
                    latest.get(
                        "status",
                        "Planning"
                    ),

                "actual_hours":
                    total_hours

            }

        )

    else:

        Task.update(

            task_id,

            {

                "progress": 0,

                "status": "Planning",

                "actual_hours": 0

            }

        )

    flash(

        "Task update deleted.",

        "success"

    )

    return redirect(

        url_for(
            "tasks.detail",
            task_id=task_id
        )

    )


# ============================================================
# TASK UPDATE TIMELINE
# ============================================================

@task_updates_bp.route(
    "/<task_id>/updates",
    methods=["GET"]
)
@login_required
def index(task_id):
    """
    Return the activity timeline for a task.

    Currently this redirects to the task detail page.
    Later this can become a dedicated activity page or
    JSON API endpoint.
    """

    task = get_task_for_user(task_id)

    if not task:

        flash(
            "Task not found.",
            "danger"
        )

        return redirect(
            url_for("tasks.index")
        )

    return redirect(

        url_for(
            "tasks.detail",
            task_id=task_id
        )

    )