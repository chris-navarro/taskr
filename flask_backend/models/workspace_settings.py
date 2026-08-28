from flask_backend.database import mongo


class WorkspaceSettings:
    COLLECTION = "workspace_settings"
    KEY = "task_categories"
    DEFAULT_CATEGORIES = [
        "Development",
        "Research",
        "Documentation",
        "Testing",
        "Deployment",
        "Engagement",
        "SME",
        "NDD Review",
    ]

    @classmethod
    def collection(cls):
        return mongo.db[cls.COLLECTION]

    @classmethod
    def categories(cls):
        document = cls.collection().find_one({"_id": cls.KEY})
        categories = document.get("values", []) if document else []
        return list(dict.fromkeys(cls.DEFAULT_CATEGORIES + categories))

    @classmethod
    def add_category(cls, category):
        category = " ".join(category.split())
        if not category:
            return False
        result = cls.collection().update_one(
            {"_id": cls.KEY},
            {"$addToSet": {"values": category}},
            upsert=True,
        )
        return result.modified_count > 0 or result.upserted_id is not None

    @classmethod
    def remove_category(cls, category):
        if category in cls.DEFAULT_CATEGORIES:
            return False
        result = cls.collection().update_one(
            {"_id": cls.KEY},
            {"$pull": {"values": category}},
        )
        return result.modified_count > 0
