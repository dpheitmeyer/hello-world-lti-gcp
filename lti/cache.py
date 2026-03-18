import time

from pylti1p3.cache import CacheDataStorage


class FirestoreCache(CacheDataStorage):
    """pylti1p3 cache backed by Firestore for stateless Cloud Functions."""

    _collection = "lti_cache"

    def __init__(self, db):
        self._db = db

    def get(self, key):
        doc = self._db.collection(self._collection).document(key).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        if data.get("expires_at") and data["expires_at"] < time.time():
            return None
        return data.get("value")

    def set(self, key, value, exp=None):
        doc_data = {"value": value}
        if exp:
            doc_data["expires_at"] = time.time() + exp
        self._db.collection(self._collection).document(key).set(doc_data)
