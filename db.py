# db.py
import toml
from pymongo import MongoClient
import os

def get_db_connection():
    try:
        # Load secrets from .streamlit/secrets.toml (for Streamlit Cloud) or environment variables
        if os.path.exists(".streamlit/secrets.toml"):
            secrets = toml.load(".streamlit/secrets.toml")
            mongo_uri = f"mongodb+srv://{secrets['mongo']['username']}:{secrets['mongo']['password']}@{secrets['mongo']['host']}/{secrets['mongo']['database']}?retryWrites=true&w=majority"
        else:
            # Fallback to environment variables for local testing or other platforms
            mongo_uri = f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DATABASE')}?retryWrites=true&w=majority"

        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        # Test the connection
        client.server_info()  # Raises an exception if connection fails
        db = client[os.getenv('MONGO_DATABASE', 'chatbot_db')]  # Default to 'chatbot_db' if not set
        return db
    except Exception as e:
        raise Exception(f"Failed to connect to MongoDB: {str(e)}")

# Example usage (optional, for testing)
if __name__ == "__main__":
    db = get_db_connection()
    print("Connected to database:", db.name)