import sys
import os

BACKEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from agent4_resolver import PartResolver
from db import get_db

def main():
    db = get_db()
    resolver = PartResolver(db)
    
    queries = [
        "not the brake pads",
        "already replaced alternator",
        "brakes are fine",
        "new battery",
        "alternator",
        "brake pads"
    ]
    
    for q in queries:
        ranked = resolver.resolve_ranked(q, k=3)
        res = resolver.resolve(q)
        print(f"Q: '{q}' -> Top 3: {ranked} | Method: {res['method']}")

if __name__ == "__main__":
    main()
