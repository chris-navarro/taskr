
# Taskr

## Your Workday, Remembered

Taskr is a practical task manager that grows into a personal work journal.
It helps you capture what you planned, what you actually did, what got in the
way, and what should happen next.

That means Taskr is useful on day one for a single person managing tasks, and
useful months later when you need to answer questions such as:

- What did I accomplish this week?
- Where did my time go this month?
- Which milestones are at risk?
- How much work was completed during a performance period?
- What changed in a historical work record?

Taskr turns those answers into a searchable, linked history instead of forcing
you to reconstruct them from memory, chat messages, and scattered documents.

## Why Teams Use Taskr

Taskr combines three familiar tools in one focused workspace:

1. **Task management** for planning and tracking delivery.
2. **A work journal** for recording accomplishments, blockers, hours, and next steps.
3. **Reporting and analytics** for turning those records into useful conversations.

It is designed to be approachable for beginners while still giving managers
and administrators the detail they need for planning, reviews, and accountability.

## Feature Tour

### Dashboard at a Glance

The dashboard gives you an immediate view of your workload:

- Total tasks
- Average progress
- Tasks in progress
- Completed tasks
- Milestone Watch cards
- Timeline health indicators
- Lifecycle badges such as `New`, `Updated`, `Completed`, and `Cancelled`

Milestone cards link directly to the related task, so a summary is always one
click away from the full record.

The dashboard also provides direct access to Calendar, Kanban, Work Journal,
and Progress History views. Project progress and upcoming deadlines sit beside
each other so planning information is easy to compare.

### Task Management

Create and manage tasks with:

- Subject and project identifier
- Category and milestone
- Description and completion criteria
- Priority and status
- Start date and due date
- Estimated hours and actual hours
- Tags and parent-task relationships
- Soft deletion for safer task removal

Every task has a detail page containing its current state, progress, dates,
milestone, tags, and historical Activity Timeline.

### Historical Work Logs

A work log is the journal entry behind your progress. Record:

- The date and time when work happened, including backdated entries
- Progress percentage
- Hours worked
- Accomplishments
- Blockers or challenges
- Next steps
- Remarks and date-change justifications

Work logs are ordered chronologically on the task detail page. Editing or
deleting a log recalculates the task's current progress, status, and total
hours.

### Reports for Every Conversation

The Work Journal supports:

- Weekly reports
- Monthly reports
- Mid-year reports
- Year-end reports
- Custom From/To reporting periods

Reports include accomplishment entries, hours, update counts, completed work,
status breakdowns, category breakdowns, and daily hours activity.

### Exports

Download reports for sharing, archiving, or performance conversations as:

- CSV for spreadsheets and data analysis
- PDF for a polished printable report
- DOCX for a report you can edit and extend

Exports use the same period and filters as the report page.

### Productivity Analytics

Taskr provides lightweight, understandable measures instead of hiding your
work behind an unexplained score:

- Completion rate
- Accomplishment rate
- Planned-hours utilization
- Active work days
- Planned versus actual hours
- Comparison with the previous reporting period
- Hours by day
- Updates by category and status

These measures are intended as conversation starters and planning signals,
not as a replacement for human judgment.

### Progress History and Gantt View

Progress History displays each task's planned date window, current progress,
and historical progress markers. The calendar axis helps you see the project
window, while markers show how progress changed over time.

### Calendar and Kanban Views

Kanban groups your tasks by status and supports drag-and-drop status changes.
Each move opens a full work-update form, so the change records progress, hours,
accomplishments, blockers, and next steps in the task history. The view is
scoped to the signed-in user.

### Excel Export

Work Journal reports can also be downloaded as `.xlsx` files. The spreadsheet
contains task, category, worked date, progress, hours, status, accomplishment,
blocker, next-step, and remarks columns, making it ready for spreadsheet
analysis without rebuilding the report by hand.

### Administrator Controls

Administrators can:

- Add task categories for their team's vocabulary
- Keep categories relevant to the work, such as `Engagement`, `SME`, or `NDD Review`
- Review the update audit trail
- See snapshots recorded before historical work logs are edited or deleted

Regular users can use the journal, reports, filters, and exports for their own
tasks. Audit records are restricted to administrators.

## Quick Start

### What You Need

- Python 3.10 or newer
- MongoDB running locally or an accessible MongoDB deployment, **or SQLite3**
- A modern web browser

### 1. Get the Project

```bash
git clone <your-repository-url>
cd taskr
```

If you already have the project folder, simply open a terminal in its root.

### 2. Create a Virtual Environment

Linux and macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The dependency list includes Flask, Flask-Login, Flask-Bcrypt, PyMongo,
ReportLab, and python-docx. ReportLab powers PDF export and python-docx powers
DOCX export.

### 4. Configure the Environment

Create a `.env` file in the project root. The default backend is MongoDB:

```dotenv
SECRET_KEY=replace-this-with-a-long-random-secret
DB_BACKEND=mongo
MONGO_URI=mongodb://localhost:27017/taskr
```

The application defaults to the local MongoDB URI shown above, but setting it
explicitly makes the deployment easier to understand. Never commit real
secrets to source control.

### SQLite3 Fallback

MongoDB is the normal production-oriented backend, but Taskr can run without a
MongoDB server. SQLite3 is built into Python, so it is a convenient fallback
for local development, training, demos, small personal deployments, or
environments where installing MongoDB is not practical.

Change your `.env` file to:

```dotenv
SECRET_KEY=replace-this-with-a-long-random-secret
DB_BACKEND=sqlite
SQLITE_PATH=taskr.sqlite3
```

Then start Taskr normally:

```bash
python app.py
```

Taskr creates the SQLite file automatically on first use. The fallback stores
users, tasks, work logs, categories, and audit records in a local SQLite
database. The file is ignored by Git through `.gitignore`.

SQLite mode keeps the same application screens and workflows: login, tasks,
historical updates, reports, exports, progress history, categories, and the
administrator audit trail. No separate SQLite server is required.

### Validate the SQLite Database

Taskr's SQLite fallback uses a document-style table rather than separate
relational tables. Each record is stored in `documents`, identified by its
`collection`, with application fields inside the JSON `body` column.

Before inspecting or copying the database, stop Taskr and make a backup:

```bash
cp taskr.sqlite3 taskr.sqlite3.backup
```

If the SQLite command-line program is installed, open the database:

```bash
sqlite3 taskr.sqlite3
```

Then run these read-only checks:

```sql
-- Database integrity: expected result is `ok`.
PRAGMA integrity_check;

-- Confirm the Taskr storage table exists.
.tables
SELECT name, sql
FROM sqlite_master
WHERE type = 'table';

-- Count records in every Taskr collection.
SELECT collection, COUNT(*) AS records
FROM documents
GROUP BY collection
ORDER BY collection;

-- List users without exposing password hashes.
SELECT id,
     json_extract(body, '$.username') AS username,
     json_extract(body, '$.fullname') AS fullname,
     json_extract(body, '$.role') AS role
FROM documents
WHERE collection = 'users';

-- Review tasks and their current state.
SELECT id,
     json_extract(body, '$.subject') AS subject,
     json_extract(body, '$.status') AS status,
     json_extract(body, '$.progress') AS progress,
     json_extract(body, '$.estimated_hours') AS estimated_hours,
     json_extract(body, '$.actual_hours') AS actual_hours,
     json_extract(body, '$.created_at.value') AS created_at
FROM documents
WHERE collection = 'tasks'
ORDER BY created_at DESC;

-- Review historical work logs.
SELECT id,
     json_extract(body, '$.task_id.value') AS task_id,
     json_extract(body, '$.worked_at.value') AS worked_at,
     json_extract(body, '$.progress') AS progress,
     json_extract(body, '$.hours_worked') AS hours,
     json_extract(body, '$.status') AS status
FROM documents
WHERE collection = 'task_updates'
ORDER BY worked_at DESC;

-- Total recorded hours.
SELECT ROUND(SUM(CAST(json_extract(body, '$.hours_worked') AS REAL)), 2) AS total_hours
FROM documents
WHERE collection = 'task_updates';

-- Check audit entries.
SELECT id,
     json_extract(body, '$.action') AS action,
     json_extract(body, '$.update_id') AS update_id,
     json_extract(body, '$.created_at.value') AS recorded_at
FROM documents
WHERE collection = 'task_update_audit'
ORDER BY recorded_at DESC;
```

Exit the SQLite shell with `.quit` or `Ctrl+D`.

If the `sqlite3` command is not installed, use Python, which is already part of
the Taskr runtime:

```bash
venv/bin/python - <<'PY'
import sqlite3

connection = sqlite3.connect("taskr.sqlite3")
print(connection.execute("PRAGMA integrity_check").fetchone()[0])
print(connection.execute("""
  SELECT collection, COUNT(*)
  FROM documents
  GROUP BY collection
  ORDER BY collection
""").fetchall())
connection.close()
PY
```

Useful interpretations:

- `ok` from `PRAGMA integrity_check` means the file passes SQLite's integrity check.
- A `users` count greater than zero means an account exists in this SQLite file.
- A `tasks` count of zero means the account has no stored tasks in this backend.
- A `task_updates` count of zero means no historical work has been recorded.
- A missing collection is normal until that feature stores its first record.
- Password hashes should never be printed, copied into reports, or committed.

MongoDB and SQLite are alternative backends, not synchronized replicas. A
database created in one mode will not automatically appear in the other mode.
If you switch modes, either start with a fresh database or create a dedicated
data migration before expecting existing records to appear.

To create the local administrator while SQLite mode is enabled, run:

```bash
DB_BACKEND=sqlite SQLITE_PATH=taskr.sqlite3 python create_admin.py
```

On Windows PowerShell:

```powershell
$env:DB_BACKEND="sqlite"
$env:SQLITE_PATH="taskr.sqlite3"
python create_admin.py
```

### 5. Start MongoDB (MongoDB mode only)

If `DB_BACKEND=mongo`, make sure MongoDB is running before starting Taskr. The
application stores users, tasks, work logs, workspace categories, and audit
records in MongoDB. Skip this step when using `DB_BACKEND=sqlite`.

### 6. Create an Administrator

The development helper creates an administrator account using the configured
backend:

```bash
python create_admin.py
```

The helper currently creates:

```text
Username: devuser
Password: devpasswd
Role: Administrator
```

Change the development password before using this outside a local test
environment. For production, create users through a secure provisioning flow.

### Choosing a Backend

| Situation | Recommended backend |
| --- | --- |
| Existing MongoDB deployment | MongoDB |
| Local development without MongoDB | SQLite3 |
| Classroom or product demonstration | SQLite3 |
| Several application instances sharing data | MongoDB |
| Large, concurrent production workload | MongoDB |

SQLite is excellent for getting started and for a single application process.
MongoDB is the better choice when multiple instances, larger workloads, or
centralized database operations are required.

### Change Storage from the Admin Page

After signing in as an administrator, open **Administration** and find
**Backend storage**. Select MongoDB or SQLite3, enter the required connection
details, and choose **Test and save storage**.

The **Check connection** button runs the same availability test without writing
anything. It reports whether the selected driver is installed and whether the
backend is reachable with the values currently in the form. The page also
shows the health of the backend currently used by the running application.

Taskr performs a connectivity check before writing anything. MongoDB settings
are tested with a short timeout and SQLite settings are tested by opening the
configured file path. If the check fails, the `.env` file is left unchanged.

The check endpoint is available only to authenticated administrators at
`/admin/storage/check`; it is not a public database diagnostic endpoint.

For MongoDB, you may provide a complete URI or provide a URI plus username and
password. Taskr URL-encodes supplied credentials and stores the resulting URI
in the local `.env` file. The password is not shown again in the admin page or
in error messages.

The new configuration applies after Taskr automatically restarts. The save
request returns its success response first, then the direct Flask process
replaces itself and reloads `.env`. This restart is intentional: database
clients are initialized when the Flask application starts, and changing a live
connection underneath active requests is unsafe.

The administrator is also logged out as part of this change. Sign in again
after the restart so the new backend session is created cleanly. Taskr updates
the current process environment as well as `.env`; this prevents an inherited
old `DB_BACKEND` environment variable from overriding the newly selected
backend during the restart.

When running behind Gunicorn, Docker, systemd, or another process manager,
configure that manager to restart the web process after the storage settings
change. Process managers own the application lifecycle and should be allowed
to restart workers rather than having an individual worker replace itself.

**Important:** database storage must be provisioned and reachable before using
the settings form. Changing the backend does not migrate or copy existing
records. Back up the current database and plan a migration before switching a
real installation.

Recommended practice:

- Use SQLite3 for a single-user local installation, testing, or a demo.
- Use MongoDB for shared deployments and multiple application processes.
- Keep `.env` permissions private; Taskr attempts to set them to `600` on Unix-like systems.
- Use a secrets manager instead of storing credentials in `.env` for production.
- Use a dedicated MongoDB user with only the permissions Taskr needs.
- Back up data before changing storage configuration.

### 7. Run Taskr

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser and sign
in.

## Your First Five Minutes

1. Sign in with your account.
2. Select **Open Tasks**.
3. Create a task with a subject, dates, category, milestone, and estimated hours.
4. Open the task and select **Update Progress**.
5. Record what you accomplished, how many hours you worked, and what comes next.
6. Return to the dashboard to see the milestone card and progress indicators.
7. Open **Work Journal** to view the entry in a weekly or monthly report.

The most valuable habit is simple: write the accomplishment while it is still
fresh. A short, specific note is more useful than a vague paragraph later.

## Writing Better Work Logs

Think of each update as a small, useful answer to four questions:

| Question | Good example |
| --- | --- |
| What changed? | Completed authentication middleware. |
| How far along is it? | Progress is now 65%. |
| What slowed me down? | Waiting for API credentials. |
| What happens next? | Begin API integration. |

Keep milestone details short and descriptive. For example, use **API
integration ready** rather than a full project description. Put the detail in
the accomplishment, blocker, or next-steps fields.

Backdating is supported when work was done earlier but recorded later. If you
change a task's start or due date, provide a justification so the history
explains why the plan changed.

## Main Pages and Routes

| Page | Purpose |
| --- | --- |
| `/login` | Sign in |
| `/dashboard` | Workload summary and milestone cards |
| `/tasks/` | Search, create, edit, and manage tasks |
| `/tasks/<task_id>` | Task details and activity timeline |
| `/journal/` | Reports, filters, scorecards, and comparisons |
| `/journal/gantt` | Progress history with calendar axis |
| `/journal/export.csv` | Spreadsheet-friendly export |
| `/journal/export.pdf` | Printable report export |
| `/journal/export.docx` | Editable document export |
| `/admin` | Administrator settings |
| `/admin/audit` | Administrator-only work-log audit trail |
| `/admin/activity` | Administrator-only user activity report |
| `/admin/activity.csv` | Administrator-only activity export |

Routes require authentication unless stated otherwise. Task and report data
is scoped to the signed-in user.

## Data Model in Plain English

Taskr keeps current state and historical events separate:

- A **task** stores the current subject, dates, status, progress, estimates,
  and planning details.
- A **task update** stores a historical event: what happened, when it happened,
  progress at that moment, hours, blockers, and next steps.
- A **workspace setting** stores administrator-managed categories.
- An **audit log** stores administrator-visible snapshots before a work log is
  edited or deleted.
- A **user activity log** records authenticated views, actions, successful
  logins, failed login attempts, and logouts for administrator review.

Activity logs intentionally store route, method, result status, timestamp, and
user identity. They do not store passwords, password hashes in reports, or
submitted form contents.

This design means a task can show its current state without losing the story
of how it got there.

## Project Structure

```text
taskr/
├── app.py                         # Application entry point
├── config.py                      # Environment-backed configuration
├── create_admin.py                # Local administrator helper
├── requirements.txt               # Python dependencies
├── flask_backend/
│   ├── __init__.py                # Flask app factory and blueprint setup
│   ├── routes.py                  # Authentication, dashboard, admin routes
│   ├── tasks.py                   # Task CRUD and progress updates
│   ├── task_updates.py            # Historical update CRUD
│   ├── journal.py                 # Reports, exports, analytics, Gantt view
│   ├── database.py                # MongoDB extension setup
│   ├── extensions.py              # Flask extensions
│   ├── models/
│   │   ├── task.py
│   │   ├── task_update.py
│   │   ├── user.py
│   │   ├── workspace_settings.py
│   │   └── audit_log.py
│   ├── templates/                 # Jinja pages and Bootstrap modals
│   └── static/                    # CSS and browser JavaScript
└── README.md
```

## Common Troubleshooting

### The application cannot connect to MongoDB

Check that MongoDB is running and that `MONGO_URI` points to the correct
server and database. For local development, use:

```text
mongodb://localhost:27017/taskr
```

### PDF or DOCX export fails

Install the project dependencies inside the active virtual environment:

```bash
pip install -r requirements.txt
```

ReportLab is required for PDF files and python-docx is required for DOCX files.

### A report is empty

Reports are based on the **worked date** of historical updates, not only the
task creation date. Check the selected period and filters. A task without a
work update will not produce a journal entry for that period.

### A task does not appear in a report

Clear the category, status, and project filters, then select a wider date
range. Also confirm that the task belongs to the signed-in user.

### A milestone looks behind schedule

Timeline health compares the task's progress with the percentage of its date
window that has elapsed. A task past its due date is marked beyond timeline;
an incomplete task substantially behind expected progress is marked at risk.

## Development Checks

Compile the backend modules:

```bash
venv/bin/python -m py_compile app.py flask_backend/*.py flask_backend/models/*.py
```

Check patch whitespace when working in a Git checkout:

```bash
git diff --check
```

## Security Notes

- Use a strong, private `SECRET_KEY` outside local development.
- Do not commit `.env` files or passwords.
- Run behind a production WSGI server such as Gunicorn rather than Flask's
  development server.
- Use HTTPS in deployed environments.
- Review MongoDB access controls and network exposure.
- Audit access is administrator-only, and historical update edits/deletions
  require ownership of the task update.

## Roadmap

The architecture is ready for further work, including:

- Scheduled report delivery
- More chart types and period-over-period trends
- Planned-versus-actual analysis by category or project
- Team-level dashboards for managers
- Richer Gantt calendar scaling
- Configurable retention and audit policies
- Secure user provisioning and password reset flows

## Objective Revalidation

The current implementation now covers the single-user foundation and the main
visual/reporting workflow:

| Objective | Current state |
| --- | --- |
| MongoDB and SQLite3 storage | Implemented and selectable by administrators |
| Authentication and RBAC | Implemented |
| Task and historical update CRUD | Implemented |
| Dashboard widgets and milestone cards | Implemented |
| Gantt progress history with date axis | Implemented |
| Calendar view | Deferred |
| Drag-and-drop Kanban with historical updates | Implemented |
| Weekly through year-end reports | Implemented |
| CSV, PDF, DOCX, and Excel export | Implemented |
| Productivity analytics and comparison trends | Implemented |
| Admin audit and user activity reports | Implemented |
| Notifications and email reminders | Not implemented |
| AI summaries | Not implemented |
| Team collaboration and team-level reporting | Deliberately deferred |

Team-level reporting should be the next major phase. It should introduce shared
team/project ownership, membership and visibility rules, manager rollups, and
careful aggregation of individual activity. Building it after the current
single-user workflow is stable avoids mixing personal and team metrics and
makes permissions easier to reason about.

## License

No license has been declared yet. Add a license before distributing Taskr or
accepting external contributions.

## Final Word

Taskr is built around a useful idea: progress is more than a percentage. It is
the combination of intent, effort, evidence, obstacles, and next action.

Record the work once, and Taskr helps you use it many times: to plan tomorrow,
write this week's accomplishments, prepare for a performance conversation, or
explain how a project reached its current state.
