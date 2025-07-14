from pymongo import MongoClient
from datetime import datetime
import uuid
import time
# Connexion à MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['chatbot_db']
qa_collection = db['qa']
unanswered_collection = db['unanswered']
usage_collection = db['usage_stats']
# --------------------- GESTION UTILISATEUR & SESSION ---------------------
# Génère un ID unique par session
user_id = str(uuid.uuid4())
session_start_time = time.time()
# --------------------- TRAITEMENT DES QUESTIONS ---------------------
def get_exact_answer(question):
    """
    Cherche une réponse exacte dans la collection 'qa'.
    Enregistre automatiquement la question, la réponse, le temps, etc.
    """
    start_time = time.time()
    result = qa_collection.find_one({'question': question})
    end_time = time.time()
    response_time = round(end_time - start_time, 2)
    if result:
        answer = result['réponse']
        # Enregistrement de la question répondue
        qa_collection.insert_one({
            'question': question,
            'answer': answer,
            'timestamp': datetime.now(),
            'resolved': True,
            'response_time': response_time,
            'user_id': user_id})
        return answer
    else:
        # Si pas de réponse, enregistrer comme non résolue
        save_unanswered_question(question)
        return "Désolé, je n'ai pas encore la réponse à cette question."
def save_unanswered_question(question):
    """
    Sauvegarde une question sans réponse dans 'qa' et 'unanswered'.
    """
    now = datetime.now()
    # Ne pas dupliquer dans 'unanswered'
    if not unanswered_collection.find_one({'question': question}):
        unanswered_collection.insert_one({'question': question, 'timestamp': now})
    # Enregistrement dans 'qa' pour suivi
    qa_collection.insert_one({
        'question': question,
        'answer': "",
        'timestamp': now,
        'resolved': False,
        'response_time': None,
        'user_id': user_id})
# --------------------- ENREGISTREMENT DES STATS DE SESSION ---------------------
def save_session():
    """
    À appeler à la fin de la session (avant fermeture par exemple).
    Enregistre la durée de la session dans 'usage_stats'.
    """
    session_end_time = time.time()
    duration_minutes = round((session_end_time - session_start_time) / 60, 2)
    usage_collection.insert_one({
        'user_id': user_id,
        'date': datetime.now(),
        'duration': duration_minutes})
    

    
