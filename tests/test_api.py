def test_healthz_import():
    from api.main import app
    assert app is not None
