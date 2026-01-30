from app.core.security import verify_token
from app.database.database import get_db
from app.models.users import User
from app.models.history import AnswersHistory
from sqlalchemy.orm import Session
from fastapi import Depends
from fastapi import APIRouter, HTTPException
from app.rag.chain import query_rag
from app.schemas.schemas import QueryRequest, QueryResponse , HistoryResponse, HistoryEntry

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def ask_rag(request: QueryRequest ,  payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)):

    username = payload.get("sub")
    current_user = db.query(User).filter(User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    """
    Pose une question à l'assistant RAG.
    """
    try:
        response_text, elapsed_time, num_vectors = query_rag(request.question)
        
        # Enregistrer dans l'historique
        history_entry = AnswersHistory(
            user_id=current_user.id,
            answer=response_text,
            question=request.question,
            latency_ms=round(elapsed_time * 1000, 2),
            cluster=num_vectors
        )
        db.add(history_entry)
        db.commit()
    
        return QueryResponse(answer=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/history", response_model=HistoryResponse)
def get_history(payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)):
    """
    Récupère l'historique des questions et réponses de l'utilisateur.
    """
    username = payload.get("sub")
    current_user = db.query(User).filter(User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    
    history_entries = db.query(AnswersHistory).filter(AnswersHistory.user_id == current_user.id).all()
    
    return HistoryResponse(history=[HistoryEntry(question=entry.question, answer=entry.answer, timestamp=entry.timestamp, latency_ms=entry.latency_ms, cluster=entry.cluster) for entry in history_entries])