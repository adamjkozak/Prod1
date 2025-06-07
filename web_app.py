from flask import Flask, request, redirect, url_for, render_template_string
from task_tracker import TaskTracker

app = Flask(__name__)
tracker = TaskTracker()

TEMPLATE = """
<!doctype html>
<title>Task Tracker</title>
<h1>Tasks</h1>
<form method="post" action="/add">
    <input type="text" name="description" placeholder="Task description" required>
    <input type="number" name="priority" value="1" min="1">
    <input type="date" name="due_date">
    <button type="submit">Add Task</button>
</form>
<ul>
{% for tid, desc, priority, due, done in tasks %}
<li>
    [{{tid}}] {{desc}} (p={{priority}}){% if due %} due {{due}}{% endif %} - {{'done' if done else 'pending'}}
    {% if not done %}
    <form method="post" action="/done/{{tid}}" style="display:inline;">
        <button type="submit">Done</button>
    </form>
    {% endif %}
</li>
{% endfor %}
</ul>
"""

@app.route("/")
def index():
    tasks = tracker.list_tasks(show_all=True)
    return render_template_string(TEMPLATE, tasks=tasks)

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

if __name__ == "__main__":
    app.run()
