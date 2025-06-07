import sqlite3
import argparse
from typing import List, Tuple, Optional

DB_FILE = "tasks.db"

class TaskTracker:
    def __init__(self, db_path: str = DB_FILE, populate_dummy: bool = False):
        self.db_path = db_path
        # Allow connection reuse across Flask's threaded request handlers
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        if populate_dummy:
            self.seed_dummy_tasks()

    def _init_db(self) -> None:
        """Initialise the tasks table and upgrade old schemas."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 1,
                due_date TEXT,
                done INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'not started',
                comment TEXT,
                color TEXT
            )
            """
        )
        # If the table existed previously without the due_date column we need
        # to add it. Older SQLite versions ignore "ADD COLUMN" if it already
        # exists which keeps the operation idempotent.
        columns = [row[1] for row in self.conn.execute("PRAGMA table_info(tasks)")]
        if "due_date" not in columns:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        if "status" not in columns:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'not started'")
            # migrate existing done flag into status
            self.conn.execute("UPDATE tasks SET status='done' WHERE done=1")
        if "comment" not in columns:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN comment TEXT")
        if "color" not in columns:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN color TEXT")
        self.conn.commit()

    def add_task(
        self,
        description: str,
        priority: int = 1,
        due_date: Optional[str] = None,
        status: str = "not started",
        comment: str = "",
        color: str = "",
    ) -> None:
        """Add a new task."""
        done = 1 if status == "done" else 0
        self.conn.execute(
            "INSERT INTO tasks(description, priority, due_date, done, status, comment, color) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (description, priority, due_date, done, status, comment, color),
        )
        self.conn.commit()

    def list_tasks(
        self,
        show_all: bool = False,
        ascending: bool = False,
        sort_by: str = "priority",
        search: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        with_status: bool = False,
        with_meta: bool = False,
    ) -> List[Tuple[int, str, int, Optional[str], int]]:
        """Return tasks with optional filtering and pagination."""
        order = "ASC" if ascending else "DESC"
        if sort_by == "due":
            null_high = "9999-12-31" if ascending else "0001-01-01"
            order_clause = f"COALESCE(due_date, '{null_high}') {order}, priority DESC"
        else:
            # default to sorting by priority
            order_clause = f"priority {order}, COALESCE(due_date, '')"

        cols = "id, description, priority, due_date, done"
        if with_status:
            cols += ", status"
        if with_meta:
            cols += ", comment, color"
        base_query = f"SELECT {cols} FROM tasks"
        clauses = []
        params: List[object] = []
        if not show_all:
            clauses.append("done=0")
        if search:
            clauses.append("description LIKE ?")
            params.append(f"%{search}%")
        if status:
            clauses.append("status=?")
            params.append(status)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"{base_query}{where} ORDER BY {order_clause}"
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def count_tasks(
        self,
        show_all: bool = False,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Return number of tasks matching the given filters."""
        base_query = "SELECT COUNT(*) FROM tasks"
        clauses = []
        params: List[object] = []
        if not show_all:
            clauses.append("done=0")
        if search:
            clauses.append("description LIKE ?")
            params.append(f"%{search}%")
        if status:
            clauses.append("status=?")
            params.append(status)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return self.conn.execute(base_query + where, params).fetchone()[0]

    def seed_dummy_tasks(self) -> None:
        """Insert a few sample tasks if the table is empty."""
        count = self.conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count:
            return
        tasks = [
            ("Buy groceries", 2, "2024-05-01"),
            ("Finish project report", 5, "2024-04-20"),
            ("Call mom", 1, "2024-04-10"),
            ("Exercise", 3, "2024-04-15"),
            ("Plan vacation", 4, "2024-06-01"),
        ]
        for desc, prio, due in tasks:
            self.add_task(desc, prio, due)

    def mark_done(self, task_id: int) -> None:
        self.conn.execute("UPDATE tasks SET done=1, status='done' WHERE id=?", (task_id,))
        self.conn.commit()

    def delete_task(self, task_id: int) -> None:
        """Delete a task permanently."""
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def update_task(
        self,
        task_id: int,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None,
        status: Optional[str] = None,
        comment: Optional[str] = None,
        color: Optional[str] = None,
    ) -> None:
        """Update an existing task's fields."""
        fields = []
        params = []
        if description is not None:
            fields.append("description=?")
            params.append(description)
        if priority is not None:
            fields.append("priority=?")
            params.append(priority)
        if due_date is not None:
            fields.append("due_date=?")
            params.append(due_date)
        if status is not None:
            fields.append("status=?")
            params.append(status)
            fields.append("done=?")
            params.append(1 if status == "done" else 0)
        if comment is not None:
            fields.append("comment=?")
            params.append(comment)
        if color is not None:
            fields.append("color=?")
            params.append(color)
        if not fields:
            return
        params.append(task_id)
        self.conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id=?", params)
        self.conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple task tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("description", help="Task description")
    add_parser.add_argument(
        "-p", "--priority", type=int, default=1, help="Priority (higher means more important)"
    )
    add_parser.add_argument(
        "-d", "--due-date", help="Optional due date as YYYY-MM-DD"
    )
    add_parser.add_argument(
        "--status",
        choices=["not started", "in progress", "done"],
        default="not started",
        help="Initial status for the task",
    )

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "-a", "--all", action="store_true", help="Show completed tasks as well"
    )
    list_parser.add_argument(
        "--asc",
        action="store_true",
        help="Sort in ascending order instead of descending",
    )
    list_parser.add_argument(
        "--sort-by",
        choices=["priority", "due"],
        default="priority",
        help="Sort tasks by priority or due date",
    )

    seed_parser = subparsers.add_parser("seed", help="Insert sample tasks")

    done_parser = subparsers.add_parser("done", help="Mark task as done")
    done_parser.add_argument("task_id", type=int, help="ID of the task to mark as done")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", type=int, help="ID of the task to delete")

    edit_parser = subparsers.add_parser("edit", help="Edit an existing task")
    edit_parser.add_argument("task_id", type=int, help="ID of the task to edit")
    edit_parser.add_argument("-d", "--description", help="New description")
    edit_parser.add_argument("-p", "--priority", type=int, help="New priority")
    edit_parser.add_argument("--due-date", help="New due date")
    edit_parser.add_argument(
        "--status",
        choices=["not started", "in progress", "done"],
        help="Updated status",
    )

    args = parser.parse_args()
    tracker = TaskTracker(populate_dummy=True)

    if args.command == "add":
        tracker.add_task(args.description, args.priority, args.due_date, args.status)
    elif args.command == "list":
        tasks = tracker.list_tasks(args.all, ascending=args.asc, sort_by=args.sort_by)
        for tid, desc, priority, due, done in tasks:
            status = "done" if done else "pending"
            due_info = f" due {due}" if due else ""
            print(f"[{tid}] (p={priority}) {desc}{due_info} - {status}")
    elif args.command == "done":
        tracker.mark_done(args.task_id)
    elif args.command == "delete":
        tracker.delete_task(args.task_id)
    elif args.command == "seed":
        tracker.seed_dummy_tasks()
    elif args.command == "edit":
        tracker.update_task(
            args.task_id,
            description=args.description,
            priority=args.priority,
            due_date=args.due_date,
            status=args.status,
        )


if __name__ == "__main__":
    main()
