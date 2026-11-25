from fastapi.testclient import TestClient
import sqlite3

def initApp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import main
    db_path = tmp_path/"test_bank.db"
    monkeypatch.setattr(main, "DB_PATH", str(db_path))
    main.init_db()

    return db_path, TestClient(main.app)

def test_missing_receiver_rolls_back(tmp_path, monkeypatch):
    # init temp app and temp db
    db_path, client = initApp(tmp_path, monkeypatch)
    # check api
    response = client.post(
        "/transfers",
        json={
            "from_id": 1,
            "to_id": 999,
            "amount": 30
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User Not Found"
    #check database
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT balance FROM accounts WHERE id = ?",
            (1,)
        ).fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == 97500

def test_insufficient_funds_keeps_balances(tmp_path, monkeypatch):
    # init temp app and temp db
    db_path, client = initApp(tmp_path, monkeypatch)
    # check api
    response = client.post(
        "/transfers",
        json={
            "from_id": 1,
            "to_id": 2,
            "amount": 100000
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User Not Found or Insufficient Amount"
    # check database
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row # name mode
        row = conn.execute(
            "SELECT id, balance FROM accounts WHERE id in (?, ?)",
            (1, 2)
        ).fetchall()
    finally:
        conn.close()
    # check result length
    assert len(row) == 2
    # check id and balance
    for i in range(2):
        assert row[i]["id"] in [1, 2]
        if row[i]["id"]  == 1:
            assert row[i]["balance"] == 97500
        elif row[i]["id"] == 2:
            assert row[i]["balance"] == 51800

def test_get_account_returns_balance(tmp_path, monkeypatch):
    # init temp app and temp db
    db_path, client = initApp(tmp_path, monkeypatch)
    # check api
    response = client.get("/accounts/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["balance"] == 97500
    response = client.get("/accounts/10")
    assert response.status_code == 404
    assert response.json()["detail"] == "User Not Found"

# test directly push to main