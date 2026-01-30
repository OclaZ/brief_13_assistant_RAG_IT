from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import os 
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
DATA_PATH = "./data/"
DB_PATH = "./vector_db"  # Chemin relatif (plus sûr)

def main():
    # 1. Chargement
    print("Chargement des PDFs...")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages.")

    if not documents:
        print("Aucun document trouvé. Vérifie le dossier data/ !")
        return

    # 2. Découpage (Chunking)
    split = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
        length_function=len
    )
    chunks = split.split_documents(documents)
    print(f"Généré {len(chunks)} chunks.")

    # 3. Génération des IDs uniques (Source:Page:Index)
    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get('source')
        page = chunk.metadata.get('page')
        current_page_id = f"{source}:{page}"

        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
        
        # On crée un ID unique pour le chunk
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        chunk.metadata['id'] = chunk_id
        last_page_id = current_page_id  # <--- C'était la ligne manquante !

    # 4. Sauvegarde dans ChromaDB
    print("Sauvegarde dans la base vectorielle...")
    add_to_chroma(chunks)
    print("✅ Ingestion terminée avec succès !")

def get_embedding_function():
    return HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

def add_to_chroma(chunks):
    # On charge la DB existante ou on la crée
    db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=get_embedding_function()
    )
    
    # Ajout des documents (Chroma gère la persistance automatiquement maintenant)
    # On utilise les IDs qu'on a générés pour éviter les doublons futurs
    ids = [chunk.metadata['id'] for chunk in chunks]
    db.add_documents(chunks, ids=ids)
    
    print(f"Nombre total de documents dans la DB: {db._collection.count()}")

if __name__ == "__main__":
    main()