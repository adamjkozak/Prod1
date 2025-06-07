# Task Tracker

This repository contains a simple task tracker backed by SQLite. Tasks can be managed either from the command line or through a lightweight web interface. Each task has a priority and an optional due date and can be marked as done when completed.

## Usage

```
python3 task_tracker.py add "Buy milk" -p 2 -d 2024-12-31
python3 task_tracker.py list
python3 task_tracker.py done 1
python3 task_tracker.py delete 2
```

To run the web app:

```
python3 web_app.py
```

On [Replit](https://replit.com) the application can be started by running
`main.py` which launches the web interface using the port provided by Replit:

```
python3 main.py
```

Run `python3 task_tracker.py --help` for all available options.

## Running Tests

Install `pytest` if it is not already available and run:

```
pytest
```
