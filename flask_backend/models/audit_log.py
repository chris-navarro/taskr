from datetime import datetime

from flask_backend.database import mongo


class AuditLog:
    COLLECTION = "task_update_audit"
    ACTIVITY_COLLECTION = "user_activity_logs"

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

    @classmethod
    def activity_collection(cls):
        return mongo.db[cls.ACTIVITY_COLLECTION]

    @classmethod
    def record_activity(cls, user_id, action, endpoint, method, status_code, path):
        return cls.activity_collection().insert_one({
            "user_id": str(user_id),
            "action": action,
            "endpoint": endpoint or "unknown",
            "method": method,
            "status_code": status_code,
            "path": path,
            "created_at": datetime.utcnow(),
        })

    @classmethod
    def activity(cls, user_id=None, action=None, start_date=None, end_date=None, limit=500):
        query = {}
        if user_id:
            query["user_id"] = str(user_id)
        if action:
            query["action"] = action
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date
        return list(cls.activity_collection().find(query).sort("created_at", -1).limit(limit))
