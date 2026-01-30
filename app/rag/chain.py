import os
import time
from dotenv import load_dotenv

# --- 1. CHARGEMENT CONFIGURATION ---
# load_dotenv() cherche par défaut à la racine ou dans le dossier courant.
# Si ton .env est bien à la racine du projet, cela fonctionnera.
load_dotenv()

# Vérification de sécurité
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Fallback : Si on ne le trouve pas, on essaie de chercher explicitement dans app/ (au cas où tu insistes)
    load_dotenv("app/.env")
    api_key = os.getenv("GOOGLE_API_KEY")
    
if not api_key:
    raise ValueError("❌ ERREUR : Clé GOOGLE_API_KEY introuvable. Vérifie l'emplacement de ton fichier .env !")

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Chemin relatif correct (supposant que tu lances uvicorn depuis la racine)
DB_PATH = "./vector_db"

# --- 2. INITIALISATION GLOBALE ---
print("Chargement du modèle d'embedding...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Connexion à la base vectorielle...")
vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
)

retriever = vector_db.as_retriever(search_kwargs={"k": 3})

print(f"Initialisation du LLM avec la clé : {api_key[:5]}...") # On affiche juste le début pour debug
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", #
    temperature=0,
    google_api_key=api_key, 
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Tu es un assistant expert pour le support IT.
Utilise STRICTEMENT le contexte ci-dessous pour répondre.
Si la réponse n’est pas dans le contexte, dis clairement : "Je ne sais pas".

--- Contexte ---
{context}
"""),
    ("human", "{question}")
])

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# --- 3. DÉFINITION DE LA CHAÎNE ---
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def query_rag(question_text: str):
    start_time = time.time()

    try:
        docs = retriever.invoke(question_text)
        context = format_docs(docs)

        answer = llm.invoke(
            prompt.format(context=context, question=question_text)
        )
        answer_text = answer.content


    except Exception as e:
        return f"Erreur lors de la génération : {str(e)}"
        
    end_time = time.time()
    elapsed_time = end_time - start_time
    num_vectors = len(docs)


    
    return answer_text, elapsed_time, num_vectors