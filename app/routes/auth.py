from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.users import User
from app.schemas.schemas import UserCreate, UserOut, LoginRequest, LoginResponse
from app.core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(tags=["Authentication"])

# --- REGISTER ---
@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Vérifier si user existe
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Username already registered"
        )

    # 2. Hasher le mot de passe (via core/security.py)
    hashed_pw = get_password_hash(user.password)

    # 3. Sauvegarder
    new_user = User(
        username=user.username,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# --- LOGIN ---
@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    # 1. Chercher l'user
    user = db.query(User).filter(User.username == credentials.username).first()

    # 2. Vérifier user ET mot de passe (via core/security.py)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # 3. Créer le token (via core/security.py)
    access_token = create_access_token(data={"sub": user.username})

    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }