import redis
import hashlib
import json
import hashlib
import time

# simple in-memory cache
cache_store = {}

def generate_cache_key(text):
    return hashlib.sha256(text.encode()).hexdigest()

def get_cache(key):
    item = cache_store.get(key)

    if not item:
        return None

    value, expiry = item

    # check expiry
    if time.time() > expiry:
        del cache_store[key]
        return None

    return value

def set_cache(key, value, ttl=900):  # 15 min
    expiry = time.time() + ttl
    cache_store[key] = (value, expiry)