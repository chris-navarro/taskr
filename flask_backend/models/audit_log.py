from datetime import datetime

from flask_backend.database import mongo


class AuditLog:
    COLLECTION = "task_update_audit"

    @classmethod
    def collection(cls):
        return mongo.db[cls.COLLECTION]

    @classmethod
    def record(cls, action, task_id, update_id, user_id, snapshot):
        return cls.collection().insert_one({
            "action": action,
            "task_id": str(task_id),
            "update_id": str(update_id),
            "user_id": str(user_id),
            "snapshot": snapshot,
            "created_at": datetime.utcnow(),
        })

    @classmethod
    def recent(cls, limit=100):
        return list(cls.collection().find().sort("created_at", -1).limit(limit))
