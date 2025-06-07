import os
import sys
from pathlib import Path

# Ensure the package root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_tracker import TaskTracker
from web_app import app


def test_add_list_done(tmp_path):
    db_path = tmp_path / "tasks.db"
    tracker = TaskTracker(str(db_path))

    tracker.add_task("task one", priority=2, due_date="2024-01-01")
    tracker.add_task("task two", priority=1)

    tasks = tracker.list_tasks()
    assert len(tasks) == 2
    assert tasks[0][1] == "task one"  # highest priority first
    assert tasks[0][3] == "2024-01-01"

    tracker.mark_done(tasks[0][0])

    remaining = tracker.list_tasks()
    assert len(remaining) == 1
    assert remaining[0][1] == "task two"

    tracker.delete_task(remaining[0][0])
    assert tracker.list_tasks() == []

    all_tasks = tracker.list_tasks(show_all=True)
    assert len(all_tasks) == 1


def test_web_app(tmp_path):
    db_path = tmp_path / "tasks.db"
    tracker = TaskTracker(str(db_path))
    app.config.update({'TESTING': True})

    with app.test_client() as client:
        # override tracker in web_app with our test tracker
        import web_app
        web_app.tracker = tracker

        client.post('/add', data={'description': 'web task', 'priority': '3'})
        resp = client.get('/')
        assert b'web task' in resp.data

        # mark done and delete via HTTP
        task_id = tracker.list_tasks()[0][0]
        client.post(f'/done/{task_id}')
        client.post(f'/delete/{task_id}')
        assert tracker.list_tasks() == []

