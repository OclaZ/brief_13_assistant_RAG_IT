from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Vérifie que l'API démarre et répond sur la racine"""
    response = client.get("/")
    # Selon votre implémentation, cela peut être 200 ou 404, adaptez le code
    assert response.status_code in [200, 404]

def test_docs_accessible():
    """Vérifie que la documentation Swagger est accessible"""
    response = client.get("/docs")
    assert response.status_code == 200