from sqlalchemy import Column, Integer, String, DateTime, ForeignKey,Float
from datetime import datetime
from app.database.database import Base

class AnswersHistory(Base):
    __tablename__ = "rag_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    answer = Column(String)
    question = Column(String)
    latency_ms = Column(Float)
    cluster = Column(Integer)