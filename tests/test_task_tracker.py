import os
import sys
from pathlib import Path

# Ensure the package root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from task_tracker import TaskTracker


def test_add_list_done(tmp_path):
    db_path = tmp_path / "tasks.db"
    tracker = TaskTracker(str(db_path))

    tracker.add_task("task one", priority=2)
    tracker.add_task("task two", priority=1)

    tasks = tracker.list_tasks()
    assert len(tasks) == 2
    assert tasks[0][1] == "task one"  # highest priority first

    tracker.mark_done(tasks[0][0])

    remaining = tracker.list_tasks()
    assert len(remaining) == 1
    assert remaining[0][1] == "task two"

    all_tasks = tracker.list_tasks(show_all=True)
    assert len(all_tasks) == 2

