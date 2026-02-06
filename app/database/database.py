import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Charger le fichier .env
load_dotenv()

# 2. Récupérer les variables
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER","localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# 3. Construire l'URL de connexion
# Format: postgresql://user:password@server:port/db_name
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Vérification (optionnelle, pour debug)
print(f"Connexion à la BDD : {POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}")

# 4. Création du moteur
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    try:
        # On tente une connexion simple
        with engine.connect() as connection:
            print(f"✅ Connexion réussie à : {SQLALCHEMY_DATABASE_URL}")
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")