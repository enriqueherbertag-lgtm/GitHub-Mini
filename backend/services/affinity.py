import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import User, Debate, Suggestion
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_text_embedding(text: str) -> list:
    """
    Genera un embedding básico para un texto.
    En producción, esto debería usar un modelo real como sentence-transformers.
    Por ahora, es un placeholder que genera un vector de 384 dimensiones con ruido determinístico.
    """
    import hashlib
    import struct
    
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    embedding = []
    for i in range(0, len(hash_bytes), 4):
        if len(embedding) >= 384:
            break
        chunk = hash_bytes[i:i+4]
        if len(chunk) == 4:
            val = struct.unpack('>f', chunk)[0]
            embedding.append(val)
    
    while len(embedding) < 384:
        embedding.append(0.0)
    
    embedding = embedding[:384]
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = (embedding / norm).tolist()
    
    return embedding

def build_user_vector(db: Session, user_id: str) -> list:
    """
    Construye el vector de intereses de un usuario combinando:
    - Lenguajes de sus repositorios
    - Tópicos de sus repositorios
    - Etiquetas de sus debates
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return [0.0] * 384
    
    components = []
    
    if user.languages:
        components.append(" ".join(user.languages))
    
    if user.topics:
        components.append(" ".join(user.topics))
    
    if user.starred_topics:
        components.append(" ".join(user.starred_topics))
    
    debates = db.query(Debate).filter(Debate.user_id == user_id).all()
    for debate in debates:
        if debate.tags:
            components.append(" ".join(debate.tags))
        components.append(debate.title)
        components.append(debate.body[:500])
    
    combined_text = " ".join(components)
    
    if not combined_text.strip():
        return [0.0] * 384
    
    return get_text_embedding(combined_text)

def update_user_embedding(db: Session, user_id: str):
    """Actualiza el embedding de un usuario y lo guarda en la base de datos."""
    embedding = build_user_vector(db, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.embedding = embedding
        db.commit()
        logger.info(f"Embedding actualizado para usuario {user_id}")
    return embedding

def get_suggestions(db: Session, user_id: str, limit: int = 10) -> list:
    """
    Obtiene sugerencias de usuarios similares usando similitud de coseno.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.embedding:
        return []
    
    embedding_str = str(user.embedding).replace('[', '{').replace(']', '}')
    
    query = text("""
        SELECT 
            u.id, u.display_name, u.github_username, u.avatar_url,
            1 - (u.embedding <=> CAST(:embedding AS vector)) AS similarity
        FROM users u
        WHERE u.id != :user_id
            AND u.is_active = true
            AND u.embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {
        "embedding": embedding_str,
        "user_id": user_id,
        "limit": limit
    }).fetchall()
    
    suggestions = []
    for row in result:
        suggestions.append({
            "user_id": str(row[0]),
            "display_name": row[1],
            "github_username": row[2],
            "avatar_url": row[3],
            "similarity": float(row[4]),
            "reasons": _build_reasons(db, user_id, str(row[0]))
        })
    
    return suggestions

def _build_reasons(db: Session, user_id: str, suggested_id: str) -> list:
    """
    Construye explicaciones de por qué se sugiere a un usuario.
    """
    reasons = []
    
    user = db.query(User).filter(User.id == user_id).first()
    suggested = db.query(User).filter(User.id == suggested_id).first()
    
    if user and suggested:
        common_langs = set(user.languages or []) & set(suggested.languages or [])
        if common_langs:
            reasons.append(f"Coinciden en lenguajes: {', '.join(list(common_langs)[:3])}")
        
        common_topics = set(user.topics or []) & set(suggested.topics or [])
        if common_topics:
            reasons.append(f"Coinciden en temas: {', '.join(list(common_topics)[:3])}")
    
    debates_user = set([d.id for d in db.query(Debate).filter(Debate.user_id == user_id).all()])
    debates_suggested = set([d.id for d in db.query(Debate).filter(Debate.user_id == suggested_id).all()])
    
    common_debates = debates_user & debates_suggested
    if common_debates:
        reasons.append("Han participado en debates similares")
    
    return reasons
