import sys
import os
import random
from datetime import datetime
import time

# Permet d'importer les modules de l'application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models.history import AnswersHistory
from app.models.users import User
# On importe la vraie fonction de RAG pour générer les réponses
from app.rag.chain import query_rag

questions_data = [
    # Hardware
    "My printer is not printing properly, it just sits in the queue.",
    "The paper is coming out of the printer with nasty black lines across it.",
    "Nothing happens when I plug devices into the USB ports.",
    "My computer beeps on startup and won't load Windows.",
    "I have a cracked screen on my smartphone, is it covered?",
    "I spilled coffee on my laptop keyboard and now it won't work.",
    "My legacy serial mouse is not detected by Windows 10.",
    "How do I add a legacy parallel printer to my new PC?",
    "The battery on my laptop drains very quickly.",
    "My computer turns on briefly and then shuts itself off again.",

    # Réseau
    "I cannot connect to the office Wi-Fi network.",
    "The network connection is intermittent and keeps failing.",
    "I can see the local network but I cannot access the Internet.",
    "I can't access the shared files on the server.",
    "My internet connection keeps dropping when it rains.",
    "The VPN is not connecting, it says server not found.",
    "I can't synchronize my email to my device.",
    "Is there a global outage with Office 365 services?",
    "I can't connect to the remote desktop from home.",
    "My download speed is incredibly slow today.",

    # Windows & OS
    "I keep getting a Blue Screen of Death (BSOD) when I launch this app.",
    "How do I check the Event Viewer to see what caused the crash?",
    "My computer is running very slowly after the last Windows Update.",
    "Where can I find the Reliability History in Windows?",
    "Task Manager shows 100% CPU usage but I'm not doing anything.",
    "How do I boot my PC into Safe Mode?",
    "The Problem Steps Recorder is not saving the file.",
    "I got an error message saying 'Driver_IRQL_NOT_LESS_OR_EQUAL'.",
    "Windows update is stuck at 35% for hours.",
    "How do I use the Performance Monitor to check memory usage?",

    # Utilisateurs
    "I forgot my password and locked myself out of the account.",
    "How do I reset my password for the email system?",
    "I think I accidentally installed a virus or malware.",
    "Can I install Candy Crush on my work laptop?",
    "My account is locked, who do I contact?",
    "I received a suspicious email asking for my login details.",
    "How do I enable two-factor authentication?",
    "The text on my screen is too small, how do I change the scaling?",
    "How do I use the Night Light feature to reduce blue light?",
    "Can I use my personal iPad to access work documents (BYOD)?",

    # Procédures
    "Where can I find the asset tag on my laptop?",
    "How do I take a screenshot on Windows?",
    "Do we have a troubleshooting guide for remote access?",
    "I need to order a new toner cartridge for the printer.",
    "How do I clean my keyboard safely?",
    "Is there a way to record my screen to show you the error?",
    "How do I use the Xbox Game Bar to record a video of my app?",
    "Can you help me set up my email on my phone?",
    "I need admin rights to install a developer tool.",
    "How do I connect to a remote registry on another PC?"
]

def populate():
    print("--- Démarrage de l'insertion avec génération RAG (Cela va prendre du temps) ---")
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("Aucun utilisateur trouvé. Créez-en un d'abord.")
            return

        user_id = user.id
        print(f"-> Utilisateur cible ID: {user_id}")

        count = 0
        for i, q in enumerate(questions_data):
            # Vérification doublon
            exists = db.query(AnswersHistory).filter(AnswersHistory.question == q).first()
            if not exists:
                print(f"[{i+1}/{len(questions_data)}] Génération pour : {q[:50]}...")
                
                # --- APPEL RÉEL AU RAG ---
                try:
                    # query_rag retourne (answer_text, elapsed_time, num_vectors)
                    answer_text, elapsed_time, _ = query_rag(q)
                    
                    history_entry = AnswersHistory(
                        user_id=user_id,
                        question=q,
                        answer=answer_text,
                        latency_ms=round(elapsed_time * 1000, 2),
                        cluster=None, # Sera calculé par le script de clustering
                        timestamp=datetime.utcnow()
                    )
                    db.add(history_entry)
                    db.commit() # On commit un par un pour voir la progression
                    count += 1
                    
                    # Petite pause pour ne pas spammer l'API Google
                    time.sleep(1) 
                    
                except Exception as api_err:
                    print(f"⚠️ Erreur lors de la génération pour '{q}': {api_err}")
                    continue
            else:
                print(f"[{i+1}/{len(questions_data)}] Déjà existant : {q[:30]}...")
        
        print(f"✅ Terminé ! {count} nouvelles réponses générées et insérées.")

    except Exception as e:
        print(f"❌ Erreur globale : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate()