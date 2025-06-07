import sqlite3
import argparse
from typing import List, Tuple

DB_FILE = "tasks.db"

class TaskTracker:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 1,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def add_task(self, description: str, priority: int = 1) -> None:
        self.conn.execute(
            "INSERT INTO tasks(description, priority, done) VALUES (?, ?, 0)",
            (description, priority),
        )
        self.conn.commit()

    def list_tasks(self, show_all: bool = False) -> List[Tuple[int, str, int, int]]:
        if show_all:
            cursor = self.conn.execute(
                "SELECT id, description, priority, done FROM tasks ORDER BY done, priority DESC"
            )
        else:
            cursor = self.conn.execute(
                "SELECT id, description, priority, done FROM tasks WHERE done=0 ORDER BY priority DESC"
            )
        return cursor.fetchall()

    def mark_done(self, task_id: int) -> None:
        self.conn.execute("UPDATE tasks SET done=1 WHERE id=?", (task_id,))
        self.conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple task tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")
    add_parser.add_argument(
        "-p", "--priority", type=int, default=1, help="Priority (higher means more important)"
    )

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "-a", "--all", action="store_true", help="Show completed tasks as well"
    )

    done_parser = subparsers.add_parser("done", help="Mark task as done")
    done_parser.add_argument("task_id", type=int, help="ID of the task to mark as done")

    args = parser.parse_args()
    tracker = TaskTracker()

    if args.command == "add":
        tracker.add_task(args.description, args.priority)
    elif args.command == "list":
        tasks = tracker.list_tasks(args.all)
        for tid, desc, priority, done in tasks:
            status = "done" if done else "pending"
            print(f"[{tid}] (p={priority}) {desc} - {status}")
    elif args.command == "done":
        tracker.mark_done(args.task_id)


if __name__ == "__main__":
    main()
