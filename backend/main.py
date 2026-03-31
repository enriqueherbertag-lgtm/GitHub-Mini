from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import redis
import json
import httpx
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.responses import RedirectResponse
import uuid

from database import get_db, engine
from models import Base, User, Debate, Event
from services.affinity import get_suggestions, update_user_embedding

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GitHub-Mini API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(REDIS_URL)

config = Config(".env")
oauth = OAuth(config)
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)

class DebateCreate(BaseModel):
    title: str
    body: str
    tags: Optional[List[str]] = []

class DebateResponse(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    tags: List[str]
    status: str
    created_at: str

class SuggestionResponse(BaseModel):
    user_id: str
    display_name: str
    github_username: str
    avatar_url: str
    similarity: float
    reasons: List[str]

@app.get("/")
def read_root():
    return {"message": "GitHub-Mini API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/auth/github")
async def auth_github(request: Request):
    """Inicia el flujo de autenticación con GitHub."""
    redirect_uri = "http://localhost:8000/auth/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """Callback después de autenticación con GitHub."""
    token = await oauth.github.authorize_access_token(request)
    user_info = await oauth.github.get("user", token=token)
    user_data = user_info.json()
    
    emails = await oauth.github.get("user/emails", token=token)
    email_data = emails.json()
    primary_email = next((e["email"] for e in email_data if e.get("primary")), None)
    
    db_user = db.query(User).filter(User.github_id == user_data["id"]).first()
    
    if not db_user:
        db_user = User(
            github_id=user_data["id"],
            github_username=user_data["login"],
            display_name=user_data.get("name"),
            avatar_url=user_data.get("avatar_url"),
            email=primary_email,
            github_token=token.get("access_token"),
            is_active=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    
    request.session["user_id"] = str(db_user.id)
    
    return RedirectResponse(url="http://localhost:3000")

@app.get("/users/me")
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Obtiene el perfil del usuario autenticado."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "id": str(user.id),
        "github_username": user.github_username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "email": user.email,
        "is_active": user.is_active,
        "affiliation": user.affiliation,
        "languages": user.languages,
        "topics": user.topics,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

@app.post("/debates")
def create_debate(
    debate: DebateCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Crea un nuevo debate. Si es el primer debate del usuario, activa la cuenta."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    existing_debates = db.query(Debate).filter(Debate.user_id == user_id).count()
    is_first_debate = (existing_debates == 0)
    
    new_debate = Debate(
        user_id=user_id,
        title=debate.title,
        body=debate.body,
        tags=debate.tags or [],
        status="open"
    )
    db.add(new_debate)
    
    if is_first_debate:
        user.is_active = True
    
    db.commit()
    db.refresh(new_debate)
    
    event = Event(
        user_id=user_id,
        event_type="new_debate",
        payload={
            "debate_id": str(new_debate.id),
            "title": debate.title,
            "tags": debate.tags
        }
    )
    db.add(event)
    db.commit()
    
    redis_client.publish("user_events", json.dumps({
        "event_type": "new_debate",
        "user_id": str(user_id),
        "debate_id": str(new_debate.id),
        "tags": debate.tags or []
    }))
    
    return {
        "id": str(new_debate.id),
        "title": new_debate.title,
        "body": new_debate.body,
        "tags": new_debate.tags,
        "status": new_debate.status,
        "created_at": new_debate.created_at.isoformat()
    }

@app.get("/debates")
def list_debates(
    request: Request,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Lista los debates públicos."""
    debates = db.query(Debate).order_by(Debate.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for debate in debates:
        user = db.query(User).filter(User.id == debate.user_id).first()
        result.append({
            "id": str(debate.id),
            "user_id": str(debate.user_id),
            "username": user.github_username if user else None,
            "avatar_url": user.avatar_url if user else None,
            "title": debate.title,
            "body": debate.body[:200],
            "tags": debate.tags,
            "status": debate.status,
            "created_at": debate.created_at.isoformat()
        })
    
    return result

@app.get("/debates/{debate_id}")
def get_debate(debate_id: str, db: Session = Depends(get_db)):
    """Obtiene un debate específico."""
    debate = db.query(Debate).filter(Debate.id == debate_id).first()
    if not debate:
        raise HTTPException(status_code=404, detail="Debate no encontrado")
    
    user = db.query(User).filter(User.id == debate.user_id).first()
    
    return {
        "id": str(debate.id),
        "user_id": str(debate.user_id),
        "username": user.github_username if user else None,
        "avatar_url": user.avatar_url if user else None,
        "title": debate.title,
        "body": debate.body,
        "tags": debate.tags,
        "status": debate.status,
        "created_at": debate.created_at.isoformat()
    }

@app.get("/suggestions", response_model=List[SuggestionResponse])
def get_user_suggestions(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Obtiene sugerencias de personas para el usuario autenticado."""
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    suggestions = get_suggestions(db, user_id, limit)
    
    return suggestions
