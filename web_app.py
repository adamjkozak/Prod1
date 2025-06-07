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
#commentBox { position: fixed; top: 20%; left: 20%; background: white; border: 1px solid #ccc; padding: 10px; display:none; }
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
    <label for="comment">Comment:</label>
    <textarea id="comment" name="comment" rows="3" cols="30"></textarea>
    <label for="color">Color:</label>
    <input id="color" type="color" name="color" value="#ffffff">
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
{% for tid, desc, priority, due, done, status, comment, color in tasks %}
    <tr style="background-color: {{color if color else ''}};">
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
            <button type="button" onclick="openComment({{tid}}, {{comment|tojson}}, {{color|tojson}})">Comment</button>
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
<div id="commentBox">
  <textarea id="commentText" rows="4" cols="40"></textarea><br>
  <input type="color" id="commentColor" value="#ffffff"><br>
  <button type="button" onclick="saveComment()">Save</button>
  <button type="button" onclick="closeComment()">Close</button>
</div>
<script>
function openComment(id, text, color){
  var box=document.getElementById('commentBox');
  box.style.display='block';
  box.dataset.id=id;
  document.getElementById('commentText').value=text||'';
  document.getElementById('commentColor').value=color||'#ffffff';
}
function closeComment(){
  document.getElementById('commentBox').style.display='none';
}
document.addEventListener('click',function(e){
  var box=document.getElementById('commentBox');
  if(box.style.display==='block' && !box.contains(e.target) && e.target.tagName!=='BUTTON'){
    box.style.display='none';
  }
});
function saveComment(){
  var id=document.getElementById('commentBox').dataset.id;
  var text=document.getElementById('commentText').value;
  var color=document.getElementById('commentColor').value;
  fetch('/comment/'+id,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'comment='+encodeURIComponent(text)+'&color='+encodeURIComponent(color)}).then(()=>{window.location.reload();});
}
</script>
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
        with_meta=True,
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
    comment = request.form.get("comment", "")
    color = request.form.get("color", "")
    tracker.add_task(description, priority, due_date, status, comment, color)
    return redirect(url_for("index"))

@app.route("/done/<int:task_id>", methods=["POST"])
def done(task_id: int):
    tracker.mark_done(task_id)
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id: int):
    tracker.delete_task(task_id)
    return redirect(url_for("index"))

@app.route("/comment/<int:task_id>", methods=["POST"])
def comment(task_id: int):
    comment = request.form.get("comment", "")
    color = request.form.get("color", "")
    tracker.update_task(task_id, comment=comment, color=color)
    return ("", 204)

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit(task_id: int):
    if request.method == "POST":
        description = request.form.get("description")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date") or None
        status = request.form.get("status")
        comment = request.form.get("comment")
        color = request.form.get("color")
        tracker.update_task(
            task_id,
            description=description,
            priority=int(priority) if priority else None,
            due_date=due_date,
            status=status,
            comment=comment,
            color=color,
        )
        return redirect(url_for("index"))
    task = tracker.conn.execute(
        "SELECT description, priority, due_date, status, comment, color FROM tasks WHERE id=?",
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
        <label>Comment:<br><textarea name=comment rows=4 cols=40>{{t[4] or ''}}</textarea></label>
        <label>Color:<input type=color name=color value=\"{{t[5] if t[5] else '#ffffff'}}\"></label>
        <button type=submit>Save</button>
    </form>
    <a href=\"/\">Back</a>
    """
    return render_template_string(edit_template, t=task, statuses=["not started", "in progress", "done"])

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
