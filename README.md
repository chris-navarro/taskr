
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
- MongoDB running locally or an accessible MongoDB deployment
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

Create a `.env` file in the project root:

```dotenv
SECRET_KEY=replace-this-with-a-long-random-secret
MONGO_URI=mongodb://localhost:27017/taskr
```

The application defaults to the local MongoDB URI shown above, but setting it
explicitly makes the deployment easier to understand. Never commit real
secrets to source control.

### 5. Start MongoDB

Make sure MongoDB is running before starting Taskr. The application stores
users, tasks, work logs, workspace categories, and audit records in MongoDB.

### 6. Create an Administrator

The development helper creates an administrator account using the configured
local MongoDB server:

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

## License

No license has been declared yet. Add a license before distributing Taskr or
accepting external contributions.

## Final Word

Taskr is built around a useful idea: progress is more than a percentage. It is
the combination of intent, effort, evidence, obstacles, and next action.

Record the work once, and Taskr helps you use it many times: to plan tomorrow,
write this week's accomplishments, prepare for a performance conversation, or
explain how a project reached its current state.
