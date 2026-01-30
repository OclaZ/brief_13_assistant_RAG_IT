from fastapi import FastAPI, HTTPException
from app.rag.chain import query_rag
from app.database.database import Base, engine
from app.schemas.schemas import QueryRequest, QueryResponse
from app.routes.query import router as query_router
from app.routes.auth import router as auth_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Support IT Assistant RAG",
    description="API pour interroger le manuel de support IT via une IA.",
    version="1.0.0"
)
app.include_router(query_router, tags=["RAG Query"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@app.get("/")
def read_root():
    return {"status": "ok", "message": "L'API Support IT est en ligne !"}



