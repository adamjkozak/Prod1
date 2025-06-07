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
    <label for="sort">Sort:</label>
    <select name="sort" id="sort" onchange="this.form.submit()">
        <option value="desc" {% if sort == 'desc' %}selected{% endif %}>Priority high-&gt;low</option>
        <option value="asc" {% if sort == 'asc' %}selected{% endif %}>Priority low-&gt;high</option>
        <option value="due" {% if sort == 'due' %}selected{% endif %}>Due date</option>
    </select>
</form>
<form method="post" action="/add">
    <label for="description">Description:</label>
    <input id="description" type="text" name="description" required>
    <label for="priority">Priority:</label>
    <input id="priority" type="number" name="priority" value="1" min="1">
    <label for="due_date">Due date:</label>
    <input id="due_date" type="date" name="due_date">
    <button type="submit">Add Task</button>
</form>
<table>
<thead>
    <tr>
        <th>ID</th>
        <th>Description</th>
        <th>Priority</th>
        <th>Due date</th>
        <th>Status</th>
        <th>Actions</th>
    </tr>
</thead>
<tbody>
{% for tid, desc, priority, due, done in tasks %}
    <tr>
        <td>{{tid}}</td>
        <td>{{desc}}</td>
        <td>{{priority}}</td>
        <td>{{due if due else ''}}</td>
        <td>{{'done' if done else 'pending'}}</td>
        <td>
            {% if not done %}
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
"""

@app.route("/")
def index():
    sort = request.args.get("sort", "desc")
    if sort == "due":
        tasks = tracker.list_tasks(show_all=True, sort_by="due", ascending=True)
    else:
        tasks = tracker.list_tasks(show_all=True, ascending=(sort == "asc"))
    return render_template_string(TEMPLATE, tasks=tasks, sort=sort)

@app.route("/add", methods=["POST"])
def add():
    description = request.form["description"]
    priority = int(request.form.get("priority", 1))
    due_date = request.form.get("due_date") or None
    tracker.add_task(description, priority, due_date)
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
        tracker.update_task(
            task_id,
            description=description,
            priority=int(priority) if priority else None,
            due_date=due_date,
        )
        return redirect(url_for("index"))
    task = tracker.conn.execute(
        "SELECT description, priority, due_date FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    edit_template = """
    <!doctype html>
    <title>Edit Task</title>
    <form method=\"post\">
        <label>Description:<input type=text name=description value=\"{{t[0]}}\"></label>
        <label>Priority:<input type=number name=priority value=\"{{t[1]}}\" min=1></label>
        <label>Due date:<input type=date name=due_date value=\"{{t[2] if t[2] else ''}}\"></label>
        <button type=submit>Save</button>
    </form>
    <a href=\"/\">Back</a>
    """
    return render_template_string(edit_template, t=task)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
