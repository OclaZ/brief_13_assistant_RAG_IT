from datetime import datetime
from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str

# Pour le Register (Sortie - on cache le mot de passe)
class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Pour le Login (Entrée)
class LoginRequest(BaseModel):
    username: str
    password: str

# Pour le Login (Sortie)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    latency_ms: float
    cluster: int

class HistoryEntry(BaseModel):
    question: str
    answer: str
    timestamp: datetime
    latency_ms: float
    cluster: int

    class Config:
        from_attributes = True
class HistoryResponse(BaseModel):
    history: list[HistoryEntry]
    class Config:
        from_attributes = True
