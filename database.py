from pymongo import MongoClient
import os

def get_db():
    MONGODB_URI = os.environ.get("MONGODB_URI")
    client = MongoClient(MONGODB_URI)
    db = client.get_database("CineBot")
    return db.posts  # Colección 'posts'