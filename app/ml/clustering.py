import sys
import os

# Ajout du dossier parent au path pour pouvoir importer 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from app.database.database import SessionLocal
from app.models.history import AnswersHistory
# --- CORRECTION ICI ---
# L'import de User est indispensable pour que SQLAlchemy résolve la clé étrangère "users.id"
from app.models.users import User 

# Configuration
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
NUM_CLUSTERS = 5

def process_clustering():
    print("--- Démarrage du clustering des questions ---")
    db = SessionLocal()
    
    try:
        # 1. Extraction des questions (seulement celles qui n'ont pas de cluster ou qu'on veut recalculer)
        records = db.query(AnswersHistory).filter(AnswersHistory.question.isnot(None)).all()
        
        if not records:
            print("Aucune donnée à traiter.")
            return

        questions = [r.question for r in records]
        ids = [r.id for r in records]
        print(f"-> {len(questions)} questions récupérées.")

        if len(questions) < NUM_CLUSTERS:
            print(f"Pas assez de données pour faire {NUM_CLUSTERS} clusters. (Minimum {NUM_CLUSTERS})")
            return

        # 2. Génération des embeddings
        print(f"-> Chargement du modèle {MODEL_NAME}...")
        model = SentenceTransformer(MODEL_NAME)
        
        print("-> Vectorisation des questions...")
        embeddings = model.encode(questions)

        # 3. Clustering non supervisé (KMeans)
        print(f"-> Application de KMeans (k={NUM_CLUSTERS})...")
        kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
        kmeans.fit(embeddings)
        labels = kmeans.labels_

        # 4. Stockage des clusters en base
        print("-> Mise à jour de la base de données...")
        for record_id, label in zip(ids, labels):
            # Utilisation de la méthode moderne Session.get()
            record = db.get(AnswersHistory, record_id)
            if record:
                record.cluster = int(label)
        
        db.commit()
        print("✅ Succès : Les clusters ont été mis à jour.")

    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    process_clustering()