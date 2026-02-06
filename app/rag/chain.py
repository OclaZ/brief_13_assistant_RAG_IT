import os
import time
import statistics
import mlflow
import mlflow.langchain
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
DB_PATH = "./vector_db"
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "RAG_Default")

# --- CONFIGURATION MLFLOW ---
mlflow.set_tracking_uri(MLFLOW_URI)
mlflow.set_experiment(EXPERIMENT_NAME)

# --- CONFIGURATION RAG ---
# Paramètres (pour pouvoir les logger plus tard)
RAG_CONFIG = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "llm_model": "gemini-2.5-flash",
    "temperature": 0.0,
    "top_k": 3
}

print("Chargement du modèle d'embedding...")
embeddings = HuggingFaceEmbeddings(model_name=RAG_CONFIG["embedding_model"])

vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
)

print(f"Initialisation du LLM...")
llm = ChatGoogleGenerativeAI(
    model=RAG_CONFIG["llm_model"],
    temperature=RAG_CONFIG["temperature"],
    google_api_key=api_key,
)

# Template du prompt
system_prompt = """Tu es un assistant expert pour le support IT.
Utilise STRICTEMENT le contexte ci-dessous pour répondre.
Si la réponse n’est pas dans le contexte, dis clairement : "Je ne sais pas".

--- Contexte ---
{context}
"""
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}")
])

# Définition de la chaîne (pour l'enregistrement dans MLflow Model Registry)
rag_chain_obj = prompt_template | llm | StrOutputParser()

def format_docs_with_score(docs_with_score):
    """Formate les documents et extrait le score moyen."""
    content = "\n\n".join(doc.page_content for doc, _ in docs_with_score)
    scores = [score for _, score in docs_with_score]
    avg_score = statistics.mean(scores) if scores else 0
    return content, avg_score, len(docs_with_score)

def query_rag(question_text: str):
    """
    Exécute le RAG avec tracking MLflow complet.
    """
    start_time = time.time()
    
    # Démarrage d'une "RUN" MLflow
    with mlflow.start_run(run_name="rag_query_execution"):
        try:
            # 1. Log des Paramètres (Configuration)
            mlflow.log_params(RAG_CONFIG)
            mlflow.log_param("prompt_template", system_prompt)

            # 2. Récupération des documents AVEC score (distance)
            # Note: Chroma renvoie une distance (plus petit = mieux). 
            # On cherche les chunks
            docs_with_score = vector_db.similarity_search_with_score(
                question_text, 
                k=RAG_CONFIG["top_k"]
            )
            
            # Préparation du contexte
            context_text, avg_distance, num_chunks = format_docs_with_score(docs_with_score)
            
            # 3. Génération de la réponse
            # On invoque la chaîne LLM avec le contexte récupéré
            answer = rag_chain_obj.invoke({
                "context": context_text,
                "question": question_text
            })
            
            elapsed_time = time.time() - start_time

            # 4. Log des Métriques
            mlflow.log_metric("latency_seconds", elapsed_time)
            mlflow.log_metric("avg_distance_score", avg_distance) # Distance L2 (0 = identique)
            mlflow.log_metric("num_chunks_retrieved", num_chunks)
            mlflow.log_metric("input_length", len(question_text))
            mlflow.log_metric("output_length", len(answer))

            # 5. Log des Inputs / Outputs (Traçabilité)
            mlflow.log_text(question_text, "input_question.txt")
            mlflow.log_text(answer, "output_answer.txt")
            mlflow.log_text(context_text, "retrieved_context.txt")

            # 6. MLflow Model Registry (Enregistrement du modèle)
            # On enregistre la chaîne utilisée pour cette requête
            # Cela permet de versionner la logique exacte utilisée.
            mlflow.langchain.log_model(
                rag_chain_obj, 
                artifact_path="rag_chain_model",
                registered_model_name="IT_Support_RAG_Chain"
            )

            return answer, elapsed_time, num_chunks

        except Exception as e:
            # En cas d'erreur, on la logue aussi dans MLflow
            mlflow.log_param("error", str(e))
            raise e