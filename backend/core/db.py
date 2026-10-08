import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "auto_triage")
MONGO_SUBSCRIPTIONS_DB = os.getenv("MONGO_SUBSCRIPTIONS_DB", "auto_triage_subscriptions")

# Module-level client. PyMongo pools connections internally and is safe to
# share across the app, so every agent reuses this single instance.
client = MongoClient(MONGO_URI)

def get_db() -> Database:
    """Return the shared Auto-Triage catalog database handle."""
    return client[MONGO_DB]

def get_subscriptions_db() -> Database:
    """Return the dedicated Auto-Triage users and subscriptions database handle."""
    return client[MONGO_SUBSCRIPTIONS_DB]
