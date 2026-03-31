import redis
import json
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
DATABASE_URL = os.getenv("DATABASE_URL")

redis_client = redis.from_url(REDIS_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from services.affinity import update_user_embedding

def process_event(event_data):
    """Procesa un evento y actualiza el embedding del usuario afectado."""
    try:
        event = json.loads(event_data)
        event_type = event.get("event_type")
        user_id = event.get("user_id")
        
        if not user_id:
            logger.warning("Evento sin user_id: %s", event)
            return
        
        logger.info("Procesando evento %s para usuario %s", event_type, user_id)
        
        db = SessionLocal()
        try:
            update_user_embedding(db, user_id)
        finally:
            db.close()
            
    except Exception as e:
        logger.error("Error procesando evento: %s", e)

def main():
    """Escucha eventos en Redis y los procesa."""
    pubsub = redis_client.pubsub()
    pubsub.subscribe("user_events")
    
    logger.info("Worker de afinidad iniciado. Esperando eventos...")
    
    for message in pubsub.listen():
        if message["type"] == "message":
            process_event(message["data"])

if __name__ == "__main__":
    main()
