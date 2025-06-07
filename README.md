# Task Tracker

This repository contains a simple command line task tracker that stores tasks in a local SQLite database. Tasks can be added with a priority, listed in priority order and marked as done.

## Usage

```
python3 task_tracker.py add "Buy milk" -p 2
python3 task_tracker.py list
python3 task_tracker.py done 1
```

Run `python3 task_tracker.py --help` for all available options.

## Running Tests

Install `pytest` if it is not already available and run:

```
pytest
```
