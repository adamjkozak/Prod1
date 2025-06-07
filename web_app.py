from flask import Flask, request, redirect, url_for, render_template_string
from task_tracker import TaskTracker

app = Flask(__name__)
tracker = TaskTracker(populate_dummy=True)

TEMPLATE = """
<!doctype html>
<title>Task Tracker</title>
<style>
table { border-collapse: collapse; width: 100%; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
tr:nth-child(even) { background-color: #f9f9f9; }
tr:nth-child(odd) { background-color: #ffffff; }
</style>
<h1>Tasks</h1>
<form method="get" action="/">
    <label for="q">Search:</label>
    <input id="q" type="text" name="q" value="{{q}}">
    <label for="status">Status:</label>
    <select name="status" id="status" onchange="this.form.submit()">
        <option value="" {% if not status_filter %}selected{% endif %}>All</option>
        {% for st in statuses %}
        <option value="{{st}}" {% if status_filter==st %}selected{% endif %}>{{st}}</option>
        {% endfor %}
    </select>
    <label for="sort">Sort:</label>
    <select name="sort" id="sort" onchange="this.form.submit()">
        <option value="desc" {% if sort == 'desc' %}selected{% endif %}>Priority high-&gt;low</option>
        <option value="asc" {% if sort == 'asc' %}selected{% endif %}>Priority low-&gt;high</option>
        <option value="due_asc" {% if sort == 'due_asc' %}selected{% endif %}>Due earliest</option>
        <option value="due_desc" {% if sort == 'due_desc' %}selected{% endif %}>Due latest</option>
    </select>
    <button type="submit">Apply</button>
</form>
<form method="post" action="/add">
    <label for="description">Description:</label>
    <input id="description" type="text" name="description" required>
    <label for="priority">Priority:</label>
    <input id="priority" type="number" name="priority" value="1" min="1">
    <label for="due_date">Due date:</label>
    <input id="due_date" type="date" name="due_date">
    <label for="status_new">Status:</label>
    <select name="status" id="status_new">
        {% for st in statuses %}
        <option value="{{st}}" {% if st=='not started' %}selected{% endif %}>{{st}}</option>
        {% endfor %}
    </select>
    <button type="submit">Add Task</button>
</form>
<table>
<thead>
    <tr>
        <th>Description</th>
        <th>Priority</th>
        <th>Due date</th>
        <th>Status</th>
        <th>Actions</th>
    </tr>
</thead>
<tbody>
{% for tid, desc, priority, due, done, status in tasks %}
    <tr>
        <td>{{desc}}</td>
        <td>{{priority}}</td>
        <td>{{due if due else ''}}</td>
        <td>{{status}}</td>
        <td>
            {% if status != 'done' %}
            <form method="post" action="/done/{{tid}}" style="display:inline;">
                <button type="submit">Done</button>
            </form>
            {% endif %}
            <form method="get" action="/edit/{{tid}}" style="display:inline;">
                <button type="submit">Edit</button>
            </form>
            <form method="post" action="/delete/{{tid}}" style="display:inline;">
                <button type="submit">Delete</button>
            </form>
        </td>
    </tr>
{% endfor %}
</tbody>
</table>
<div>
{% if page > 1 %}
  <a href="{{ url_for('index', page=page-1, sort=sort, q=q, status=status_filter) }}">Previous</a>
{% endif %}
{% if has_next %}
  <a href="{{ url_for('index', page=page+1, sort=sort, q=q, status=status_filter) }}">Next</a>
{% endif %}
</div>
"""

@app.route("/")
def index():
    sort = request.args.get("sort", "desc")
    q = request.args.get("q", "")
    status_filter = request.args.get("status") or None
    page = int(request.args.get("page", 1))
    limit = 10
    offset = (page - 1) * limit
    if sort == "due_asc":
        sort_by, ascending = "due", True
    elif sort == "due_desc":
        sort_by, ascending = "due", False
    else:
        sort_by, ascending = "priority", sort == "asc"
    tasks = tracker.list_tasks(
        show_all=True,
        sort_by=sort_by,
        ascending=ascending,
        search=q or None,
        status=status_filter,
        limit=limit,
        offset=offset,
        with_status=True,
    )
    total = tracker.count_tasks(show_all=True, search=q or None, status=status_filter)
    has_next = offset + limit < total
    return render_template_string(
        TEMPLATE,
        tasks=tasks,
        sort=sort,
        q=q,
        status_filter=status_filter,
        page=page,
        has_next=has_next,
        statuses=["not started", "in progress", "done"],
    )

@app.route("/add", methods=["POST"])
def add():
    description = request.form["description"]
    priority = int(request.form.get("priority", 1))
    due_date = request.form.get("due_date") or None
    status = request.form.get("status", "not started")
    tracker.add_task(description, priority, due_date, status)
    return redirect(url_for("index"))

@app.route("/done/<int:task_id>", methods=["POST"])
def done(task_id: int):
    tracker.mark_done(task_id)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id: int):
    tracker.delete_task(task_id)
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id: int):
    if request.method == "POST":
        description = request.form.get("description")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date") or None
        status = request.form.get("status")
        tracker.update_task(
            task_id,
            description=description,
            priority=int(priority) if priority else None,
            due_date=due_date,
            status=status,
        )
        return redirect(url_for("index"))
    task = tracker.conn.execute(
        "SELECT description, priority, due_date, status FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    edit_template = """
    <!doctype html>
    <title>Edit Task</title>
    <form method=\"post\">
        <label>Description:<input type=text name=description value=\"{{t[0]}}\"></label>
        <label>Priority:<input type=number name=priority value=\"{{t[1]}}\" min=1></label>
        <label>Due date:<input type=date name=due_date value=\"{{t[2] if t[2] else ''}}\"></label>
        <label>Status:
            <select name=status>
            {% for st in statuses %}
                <option value=\"{{st}}\" {% if t[3]==st %}selected{% endif %}>{{st}}</option>
            {% endfor %}
            </select>
        </label>
        <button type=submit>Save</button>
    </form>
    <a href=\"/\">Back</a>
    """
    return render_template_string(edit_template, t=task, statuses=["not started", "in progress", "done"])

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
