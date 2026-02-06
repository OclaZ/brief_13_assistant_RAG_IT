import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt  # On utilise bcrypt directement (plus de passlib !)

load_dotenv()

# Config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Sécurité HTTP
security = HTTPBearer()

# --- 1. FONCTIONS MOT DE PASSE (MODERNISÉES) ---
# On remplace CryptContext par des appels directs à bcrypt.
# Cela évite tous les conflits de version et les erreurs "InternalBackendError".

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe."""
    # bcrypt a besoin de bytes, pas de strings
    if plain_password is None or hashed_password is None:
        return False
    
    # On convertit les entrées (str) en bytes
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

def get_password_hash(password: str) -> str:
    """Hache un mot de passe."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    
    # On retourne une string pour le stockage en BDD
    return hashed.decode('utf-8')

# --- 2. FONCTIONS JWT ---
# (Cette partie reste identique)
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload