def test_imports():
    import scripts.init_db as db
    assert db.Base is not None
