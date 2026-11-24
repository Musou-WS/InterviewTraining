from fastapi.testclient import TestClient

def test_missing_receiver_rolls_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    import main

    db_path = tmp_path / "test_bank.db"
    monkeypatch.setattr(main, "DB_PATH", str(db_path))
    main.init_db()

    client = TestClient(main.app)

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