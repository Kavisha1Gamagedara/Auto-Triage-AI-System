import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "auto_triage")
MONGO_SUBSCRIPTIONS_DB = os.getenv("MONGO_SUBSCRIPTIONS_DB", "auto_triage_subscriptions")

# Configure robust DNS resolver fallback for Windows/ISP environments
# where router DNS (e.g. 192.168.1.1) fails to resolve MongoDB Atlas SRV records.
try:
    import dns.resolver
    _custom_resolver = dns.resolver.Resolver(configure=False)
    _custom_resolver.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]
    dns.resolver.default_resolver = _custom_resolver
except Exception as _e:
    pass

# Module-level client. PyMongo pools connections internally and is safe to
# share across the app, so every agent reuses this single instance.
client = MongoClient(MONGO_URI)

def get_db() -> Database:
    """Return the shared Auto-Triage catalog database handle."""
    return client[MONGO_DB]

def get_subscriptions_db() -> Database:
    """Return the dedicated Auto-Triage users and subscriptions database handle."""
    return client[MONGO_SUBSCRIPTIONS_DB]
