import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

class TransferRequest(BaseModel):
    from_id: int
    to_id: int
    amount: int = Field(gt=0)

import sqlite3

DB_PATH = "bank_summary_practice.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("PRAGMA foreign_keys = ON")

        # Accounts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                owner TEXT NOT NULL,
                balance INTEGER NOT NULL CHECK(balance >= 0)
            )
        """)

        # Transfers
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                amount INTEGER NOT NULL CHECK(amount > 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (from_id) REFERENCES accounts(id),
                FOREIGN KEY (to_id) REFERENCES accounts(id),
                CHECK(from_id != to_id)
            )
        """)

        # Test accounts
        conn.executemany(
            """
            INSERT OR IGNORE INTO accounts
            (id, owner, balance)
            VALUES (?, ?, ?)
            """,
            [
                (1, "Alice", 97500),
                (2, "Bob", 51800),
                (3, "Charlie", 20300),
                (4, "David", 30000),
                (5, "Emma", 8800),
                (6, "Frank", 11200)
            ]
        )

        # Test transfers
        conn.executemany(
            """
            INSERT OR IGNORE INTO transfers
            (id, from_id, to_id, amount)
            VALUES (?, ?, ?, ?)
            """,
            [
                (1, 1, 2, 2000),
                (2, 1, 3, 1000),
                (3, 2, 1, 500),
                (4, 3, 2, 700),
                (5, 5, 6, 1200)
            ]
        )

        conn.commit()

    except sqlite3.Error:
        conn.rollback()
        raise

    finally:
        conn.close()


init_db()


@app.get("/accounts/{account_id}")
def get_account(account_id: int):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        result = conn.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    except sqlite3.Error:
        raise HTTPException(
            status_code = 500,
            detail = "Database Error"
        )
    finally:
        if conn is not None:
            conn.close()
    if result is None:
        raise HTTPException(
            status_code = 404,
            detail = "User Not Found"
        )
    return {"id": result[0], "balance": result[1]}

@app.post("/transfers")
def transfer(request: TransferRequest):
    if request.from_id == request.to_id:
        raise HTTPException(
            status_code=400,
            detail="Accounts Must Be Different"
        )

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.execute("UPDATE accounts SET balance = balance - ? WHERE balance >= ? and id = ?", (request.amount, request.amount, request.from_id))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code = 404,
                detail = "User Not Found or Insufficient Amount"
            )

        cursor = conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (request.amount, request.to_id))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code = 404,
                detail = "User Not Found"
            )

        conn.execute("COMMIT")

        return "success"

    except sqlite3.Error:
        conn.execute("ROLLBACK")
        raise HTTPException(
            status_code = 500,
            detail = "Database Error"
        )

    except HTTPException:
        if conn.in_transaction:
            conn.rollback()
        raise

    finally:
        conn.close()

@app.get("/accounts/{account_id}/summary")
def get_account_summary(account_id: int):
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("select id as account_id, owner, balance, coalesce(total_incoming, 0) as total_incoming, coalesce(total_outgoing, 0) as total_outgoing, coalesce(total_incoming,0)-coalesce(total_outgoing,0) as net_flow from accounts left join (select from_id as fid, sum(amount) as total_outgoing from transfers group by from_id)  on id = fid left join (select to_id as tid, sum(amount) as total_incoming from transfers group by to_id) on id=tid where accounts.id=?", (account_id, ))
        result = cursor.fetchone() 
        if result is None:
            raise HTTPException(
                status_code = 404,
                detail = "User Not Found"
            )
        return result
    except sqlite3.Error:
        raise HTTPException(
            status_code = 500,
            detail = "Database Error"
        )
    finally:
        if conn is not None:
            conn.close()
