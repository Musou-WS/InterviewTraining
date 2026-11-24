# FastAPI Bank API

A backend practice project built with FastAPI and SQLite,
focusing on account queries, transfer transactions, and automated testing.

## Tech Stack

- Python
- FastAPI
- SQLite
- pytest and FastAPI TestClient

## Features

- Query account information and balance summaries
- Transfer funds using SQLite transactions
- Handle invalid requests and failed transfers
- Test API responses and persisted database state

## Run Locally

With the project's Python environment activated:

```bash
cd Backend
python3 -m uvicorn main:app --reload
```

Interactive API documentation:
http://127.0.0.1:8000/docs

## Run Tests

From the Backend directory:

```bash
python3 -m pytest
```

The current test covers a transfer to a nonexistent receiving account
and checks that the sender's stored balance remains unchanged.
