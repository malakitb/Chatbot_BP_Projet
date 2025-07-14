from pymongo import MongoClient
def get_db():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["chatbot_db"]
        return db
    except Exception as e:
        print("Erreur de connexion à MongoDB :", e)
        return None
def create_collections():
    db = get_db()
    if db is None:
        return
    if "qa" not in db.list_collection_names():
        db.create_collection("qa")
        print("✅ Collection 'qa' créée.")
    if "unanswered" not in db.list_collection_names():
        db.create_collection("unanswered")
        print("✅ Collection 'unanswered' créée.")
# À exécuter une seule fois pour créer les collections
if __name__ == "__main__":
    create_collections()
